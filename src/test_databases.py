#!/usr/bin/env python3
"""
Database Testing Script for SM3 Docker Deployment

Tests all four database systems to verify they are correctly deployed and accessible:
- PostgreSQL
- MongoDB
- Neo4j
- GraphDB (SPARQL)

Exit codes:
  0 - All databases pass
  1 - One or more databases fail
"""

from __future__ import annotations
import json
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

# PostgreSQL
POSTGRES_URL = "postgresql+psycopg://sm3:sm3@localhost:5432/sm3"

# MongoDB
MONGO_URI = "mongodb://sm3:sm3@localhost:27018/sm3?authSource=admin"

# Neo4j
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "password"

# GraphDB
GRAPHDB_HOST = "localhost"
GRAPHDB_PORT = "7200"
GRAPHDB_REPOSITORY = "sm3_graphdb"
GRAPHDB_USERNAME = "admin"
GRAPHDB_PASSWORD = "root"

# General settings
QUERY_TIMEOUT = 120  # seconds


# ============================================================================
# SHARED UTILITIES
# ============================================================================

def _normalize_value(v: Any) -> Any:
    """
    Make values JSON-serializable and comparable.
    Converts non-serializable types (datetime, Decimal, UUID, etc.) to strings.
    """
    try:
        json.dumps(v)
        return v
    except TypeError:
        return str(v)


def _normalize_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize all values in all rows for comparison."""
    return [
        {k: _normalize_value(v) for k, v in row.items()}
        for row in rows
    ]


def _sorted_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort rows deterministically to enable order-insensitive comparison."""
    return sorted(rows, key=lambda r: tuple(sorted(r.items())))


# ============================================================================
# BASE TESTER CLASS
# ============================================================================

class DatabaseTester(ABC):
    """Base class for database testers."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def execute_query(self, query: str) -> Tuple[List[Dict[str, Any]] | str, float]:
        """
        Execute a query and return (result_rows | error_string, elapsed_seconds).

        Returns:
            Tuple of (result, elapsed_time) where result is either:
            - List[Dict] of row dictionaries on success
            - str starting with "Error: " on failure
        """
        pass

    def run_tests(self, tests: List[Dict[str, Any]]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Run all test queries and compare against expected results.

        Args:
            tests: List of test dictionaries with 'query' and 'result' keys

        Returns:
            Tuple of (all_passed, details_list)
        """
        all_ok = True
        details = []

        for i, test in enumerate(tests, start=1):
            query = test.get("query", "").strip()
            expected = test.get("result", None)

            # Execute query
            out, elapsed = self.execute_query(query)

            # Check for execution errors
            if isinstance(out, str) and out.startswith("Error:"):
                details.append({
                    "index": i,
                    "query": query,
                    "passed": False,
                    "note": out,
                    "elapsed": elapsed,
                    "expected": expected,
                    "actual": None,
                })
                all_ok = False
                continue

            # Normalize actual results
            actual_rows = out  # type: ignore
            actual_norm = _sorted_rows(_normalize_rows(actual_rows))

            # Handle placeholder for queries without expected results
            if isinstance(expected, str) and expected.strip() == "<query result>":
                passed = False
                note = "No comparison (placeholder '<query result>' found)."
                expected_norm = None
            else:
                # Compare with expected results
                expected = expected or []
                if not isinstance(expected, list):
                    raise ValueError(
                        f"Query #{i}: 'result' must be a list of dicts or '<query result>'. "
                        f"Got: {type(expected)}"
                    )
                expected_norm = _sorted_rows(_normalize_rows(expected))
                passed = (actual_norm == expected_norm)
                note = "Matched expected result." if passed else "DIFFERENCE detected."

            details.append({
                "index": i,
                "query": query,
                "passed": passed,
                "note": note,
                "elapsed": elapsed,
                "expected": expected_norm,
                "actual": actual_norm,
            })
            all_ok = all_ok and passed

        return all_ok, details


# ============================================================================
# POSTGRESQL TESTER
# ============================================================================

class PostgreSQLTester(DatabaseTester):
    """Tester for PostgreSQL database using SQLAlchemy."""

    def __init__(self):
        super().__init__("PostgreSQL")
        self.url = POSTGRES_URL

    def execute_query(self, query: str) -> Tuple[List[Dict[str, Any]] | str, float]:
        """Execute a SQL query against PostgreSQL."""
        start = time.time()
        try:
            from sqlalchemy import create_engine, text

            engine = create_engine(self.url, future=True)
            with engine.connect() as conn:
                result = conn.execute(text(query)).mappings().all()
                rows = [dict(row) for row in result]

            return rows, time.time() - start
        except Exception as e:
            return f"Error: {e}", time.time() - start


# ============================================================================
# MONGODB TESTER
# ============================================================================

class MongoDBTester(DatabaseTester):
    """Tester for MongoDB."""

    def __init__(self):
        super().__init__("MongoDB")
        self.uri = MONGO_URI

    def execute_query(self, query: str) -> Tuple[List[Dict[str, Any]] | str, float]:
        """Execute a MongoDB aggregation query."""
        start = time.time()
        try:
            # Wrap query to ensure JSON output
            eval_code = f"JSON.stringify(({query}).toArray())"
            cmd = [
                "docker", "exec", "sm3_mongodb",
                "mongosh", "mongodb://sm3:sm3@localhost:27017/sm3?authSource=admin",
                "--quiet",
                "--eval", eval_code,
            ]

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = proc.communicate(timeout=QUERY_TIMEOUT)

            if proc.returncode != 0 and stderr.strip():
                return f"Error: {stderr.strip()}", time.time() - start
            if stderr.strip():
                return f"Error: {stderr.strip()}", time.time() - start

            # Parse JSON output
            rows = json.loads(stdout.strip())
            if not isinstance(rows, list):
                return "Error: mongosh did not return a JSON array.", time.time() - start

            return rows, time.time() - start
        except subprocess.TimeoutExpired:
            return f"Error: Query timeout ({QUERY_TIMEOUT}s)", time.time() - start
        except json.JSONDecodeError as e:
            return f"Error: JSON parse error: {e}", time.time() - start
        except Exception as e:
            return f"Error: {e}", time.time() - start


# ============================================================================
# NEO4J TESTER
# ============================================================================

class Neo4jTester(DatabaseTester):
    """Tester for Neo4j graph database using neo4j Python driver."""

    def __init__(self):
        super().__init__("Neo4j")
        self.uri = NEO4J_URI
        self.user = NEO4J_USER
        self.password = NEO4J_PASS

    def execute_query(self, query: str) -> Tuple[List[Dict[str, Any]] | str, float]:
        """Execute a Cypher query against Neo4j."""
        start = time.time()
        try:
            from neo4j import GraphDatabase

            driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            with driver, driver.session() as session:
                result = session.run(query)
                rows = [rec.data() for rec in result]

            return rows, time.time() - start
        except Exception as e:
            return f"Error: {e}", time.time() - start


# ============================================================================
# GRAPHDB TESTER (SPARQL)
# ============================================================================

class GraphDBTester(DatabaseTester):
    """Tester for GraphDB using SPARQL queries via HTTP."""

    def __init__(self):
        super().__init__("GraphDB")
        self.host = GRAPHDB_HOST
        self.port = GRAPHDB_PORT
        self.repository = GRAPHDB_REPOSITORY
        self.username = GRAPHDB_USERNAME
        self.password = GRAPHDB_PASSWORD

    def execute_query(self, query: str) -> Tuple[List[Dict[str, Any]] | str, float]:
        """Execute a SPARQL query against GraphDB."""
        start = time.time()
        try:
            import requests

            url = f"http://{self.host}:{self.port}/repositories/{self.repository}"
            headers = {"Accept": "application/sparql-results+json"}
            auth = (self.username, self.password) if self.username else None

            resp = requests.post(
                url,
                data={"query": query},
                headers=headers,
                auth=auth,
                timeout=QUERY_TIMEOUT
            )

            if resp.status_code != 200:
                return f"Error: HTTP {resp.status_code} - {resp.text.strip()}", time.time() - start

            # Parse SPARQL JSON results
            data = resp.json()
            bindings = data.get("results", {}).get("bindings", [])

            rows: List[Dict[str, Any]] = []
            for binding in bindings:
                row: Dict[str, Any] = {}
                for var, cell in binding.items():
                    row[var] = cell.get("value")
                rows.append(row)

            return rows, time.time() - start
        except requests.RequestException as e:
            return f"Error: {e}", time.time() - start
        except json.JSONDecodeError as e:
            return f"Error: JSON decode: {e}", time.time() - start
        except Exception as e:
            return f"Error: {e}", time.time() - start


# ============================================================================
# TEST QUERIES
# ============================================================================

POSTGRES_TESTS = [
    {
        "query": """
SELECT DISTINCT p.first, p.last
FROM organizations org
LEFT JOIN encounters e ON org.id = e.organization
LEFT JOIN patients p ON e.patient = p.id
WHERE org.name = 'ROYAL OF FAIRHAVEN NURSING CENTER';
""",
        "result": [{"first": "Glendora96", "last": "Tillman293"}]
    }
]

MONGODB_TESTS = [
    {
        "query": """db.organizations.aggregate([
  { $match: { "NAME": "ROYAL OF FAIRHAVEN NURSING CENTER" } },
  { $lookup: {
      "from": "patients",
      "localField": "ORGANIZATION_ID",
      "foreignField": "ENCOUNTERS.ORGANIZATION_REF",
      "as": "op"
  }},
  { $unwind: "$op" },
  { $unwind: "$op.ENCOUNTERS" },
  { $match: { "NAME": "ROYAL OF FAIRHAVEN NURSING CENTER" } },
  { $group: { "_id": { "first": "$op.FIRST", "last": "$op.LAST" } } },
  { $project: { "_id": 0, "first": "$_id.first", "last": "$_id.last" } }
])""",
        "result": [{"first": "Glendora96", "last": "Tillman293"}]
    }
]

NEO4J_TESTS = [
    {
        "query": """
MATCH (o:Organization {name: 'ROYAL OF FAIRHAVEN NURSING CENTER'})-[:IS_PERFOMED_AT]->(e:Encounter)<-[:HAS_ENCOUNTER]-(p:Patient)
RETURN DISTINCT p.firstName, p.lastName
""",
        "result": [{"p.firstName": "Glendora96", "p.lastName": "Tillman293"}]
    }
]

GRAPHDB_TESTS = [
    {
        "query": """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX syn: <https://knacc.umbc.edu/dae-young/kim/ontologies/synthea#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX pl:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#PlainLiteral>

SELECT DISTINCT ?first ?last WHERE {
  ?organization a syn:Organization;
                syn:id ?organizationId;
                syn:name 'ROYAL OF FAIRHAVEN NURSING CENTER'^^pl: .
  ?encounter a syn:Encounter;
             syn:organizationId ?organizationId;
             syn:patientId ?patientId .
  ?patient a syn:Patient;
           syn:id ?patientId;
           syn:first ?first;
           syn:last ?last .
}
""",
        "result": [{"first": "Glendora96", "last": "Tillman293"}]
    }
]


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================

def print_section_header(text: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print('=' * 70)


def print_query_result(result: Dict[str, Any]):
    """Print detailed results for a single query."""
    print(f"\n--- Query #{result['index']} ---")
    print(result['query'])
    print(f"\nPassed: {result['passed']}  |  {result['note']} (ran in {result['elapsed']:.3f}s)")

    if result['expected'] is None:
        print("\nActual rows (paste into 'result' once verified):")
        print(json.dumps(result['actual'], indent=2, ensure_ascii=False))
    elif not result['passed']:
        print("\nExpected:")
        print(json.dumps(result['expected'], indent=2, ensure_ascii=False))
        print("\nActual:")
        print(json.dumps(result['actual'], indent=2, ensure_ascii=False))


def print_summary(results: Dict[str, bool]):
    """Print final summary of all database tests."""
    print_section_header("SUMMARY")

    total = len(results)
    passed = sum(1 for p in results.values() if p)
    failed = total - passed

    for db_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}  {db_name}")

    print(f"\n{'=' * 70}")
    if failed == 0:
        print(f"✓ All {total} databases working correctly!")
    else:
        print(f"✗ {failed}/{total} databases failed")
    print('=' * 70)


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    """Run all database tests sequentially and report results."""
    print_section_header("DATABASE CONNECTIVITY TESTS")
    print("Testing all four database systems...")

    results = {}
    all_passed = True

    # Test PostgreSQL
    print_section_header("PostgreSQL Tests")
    try:
        tester = PostgreSQLTester()
        passed, details = tester.run_tests(POSTGRES_TESTS)
        for detail in details:
            print_query_result(detail)
        results["PostgreSQL"] = passed
        all_passed = all_passed and passed
    except Exception as e:
        print(f"\n✗ Failed to initialize PostgreSQL tester: {e}")
        results["PostgreSQL"] = False
        all_passed = False

    # Test MongoDB
    print_section_header("MongoDB Tests")
    try:
        tester = MongoDBTester()
        passed, details = tester.run_tests(MONGODB_TESTS)
        for detail in details:
            print_query_result(detail)
        results["MongoDB"] = passed
        all_passed = all_passed and passed
    except Exception as e:
        print(f"\n✗ Failed to initialize MongoDB tester: {e}")
        results["MongoDB"] = False
        all_passed = False

    # Test Neo4j
    print_section_header("Neo4j Tests")
    try:
        tester = Neo4jTester()
        passed, details = tester.run_tests(NEO4J_TESTS)
        for detail in details:
            print_query_result(detail)
        results["Neo4j"] = passed
        all_passed = all_passed and passed
    except Exception as e:
        print(f"\n✗ Failed to initialize Neo4j tester: {e}")
        results["Neo4j"] = False
        all_passed = False

    # Test GraphDB
    print_section_header("GraphDB (SPARQL) Tests")
    try:
        tester = GraphDBTester()
        passed, details = tester.run_tests(GRAPHDB_TESTS)
        for detail in details:
            print_query_result(detail)
        results["GraphDB"] = passed
        all_passed = all_passed and passed
    except Exception as e:
        print(f"\n✗ Failed to initialize GraphDB tester: {e}")
        results["GraphDB"] = False
        all_passed = False

    # Print summary
    print_summary(results)

    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
