# SM3-Text-to-Query: <ins>S</ins>ynthetic <ins>M</ins>ulti-<ins>M</ins>odel <ins>M</ins>edical Text-to-Query Benchmark

![Differences across query languages and database systems for the same user request](./docs/assets/querydifference.png)

This repository contains both the data and code for:

**SM3-Text-to-Query: Synthetic Multi-Model Medical Text-to-Query Benchmark**   
Authors: Sithursan Sivasubramaniam, Cedric Osei-Akoto, Yi Zhang, Kurt Stockinger, Jonathan Fürst   
**Contact: jonathan.fuerst@zhaw.ch**

[**Paper arXiv Link**](https://arxiv.org/abs/2411.05521)

This work will be presented at [NeurIPS 2024](https://neurips.cc/virtual/2024/poster/97708).
**Please cite our work if you use our data or code.**

```
@misc{sivasubramaniam2024sm3texttoquerysyntheticmultimodelmedical,
      title={SM3-Text-to-Query: Synthetic Multi-Model Medical Text-to-Query Benchmark}, 
      author={Sithursan Sivasubramaniam and Cedric Osei-Akoto and Yi Zhang and Kurt Stockinger and Jonathan Fuerst},
      year={2024},
      eprint={2411.05521},
      archivePrefix={arXiv},
      primaryClass={cs.DB},
      url={https://arxiv.org/abs/2411.05521}, 
}
```

**Note: This repository will be updated further during the next week to make it easier to set up and use the four
different databases.**

## Data

The `./data` directory contains our template questions, the Synthea data, train and dev data, and the Text-to-Query
results of our evaluated LLMs for all databases.

For detailed information about the data presented in this project, please refer to the README in the `./data` directory.

## Code

The `./src` directory contains the code to reproduce the results presented in SM3-Text-to-Query.

A more elaborate description of the code components can be found in the README of the `./src` directory.

## Getting Started

### 1. Setup DBs

The first step is to deploy the four database systems (PostgreSQL, MongoDB, Neo4j and GraphDB) and load and transform
the synthetic patient data that has been generated through [Synthea](github.com/synthetichealth/synthea).
For convenience, we provide a docker-compose file:

`docker compose up -d` will take care of deploying the docker container for the four databases, loading and transforming
the data.

> Note: Use `docker compose down` to stop the containers again. Using `docker stop container_name` might leave some
> ports blocked and prevent containers from starting properly again on some systems.

**Repository Setup (mandatory):**

Create GraphDB repository named "sm3_graphdb" by entering the GraphDB GUI on a Browser via http://localhost:7200

In the menu on the left, navigate to `Setup` and then `Repositories`. There, create a new repository and select
`GraphDB Repository`. Make sure to give it the name `sm3_graphdb` and leave the other settings on default.
Once it has been created, select the new repository with `Choose repository` in the top right corner.

If you haven't already, decompress (unzip) the [synthea_ttl.zip](data/synthea_ttl.zip) file in this git repo.
In the UI again, navigate to `Import` and select `Upload RDF files` and upload the `.ttl` files from that zip archive.
Then mark all of them and import them into GraphDB. The import can take a while depending on your system.

### 2. Test the Deployment

Setup a python venv or conda environment and install the requirements from requirements.txt
Use the [test_databases.py](src/test_databases.py) script to test the four databases. If all tests are succesful, you
are good to go.

> NOTE: The data for Neo4J and GraphDB takes a while to be loaded, so check that the GraphDB data is fully loaded, 
> before running the test. The Neo4J data should be ready by the time the GraphDB is done.

### 3. Text-to-Query

Run your own Text-to-Query system on the train/dev data.

## Data

- `./data/synthea_data` contains the Synthea data used as the basis for PostgreSQL, Graph DB (RDF), Neo4j, and MongoDB.
- `./data/dataset/train_dev`contains the annotated
  train and dev splits for all four query languages: SQL, SPARQL, Cypher, and
  MQL
- `./data/dataset/test` contains the annotated test set for all four query languages: SQL, SPARQL, Cypher, and MQL.
  The test set will not be released publicly to enable a fair evaluation
  as common practice in other Text-to-Query benchmarks such as Spider or
  BIRD, but we provide it to support the review of the paper.
- `./data/dataset/processed_data` contains different data splits, including the responses from the respective databases.
- `./data/dataset/question_templates` contains the 408 question templates used to construct SM3-Text-to-Query.
- `./data/results` contains the results for each of the
  evaluated database systems and query languages for each of the five prompts,
  the four LLMs, and the three repetitions.

## Code

- `./src/docker_configuration` contains the code to set up the four different database systems (PostgreSQL, GraphDB,
  Neo4j, and MongoDB) and populate them with Synthea data.
- `./src/run_experiments` contains the code to
  replicate our experiments for all database models, LLMs, prompts, and few-shot
  sampling (repetitions).
- `./src/evaluation` contains the code to evaluate the
  results obtained by the LLMs for our four databases, including the necessary
  data-cleaning logic. It computes Execution Accuracy (EA) and Valid Efficiency
  Score (VES) for each combination of LLM, database model, and prompt-setting.

## Croissant Metadata

```json
{
  "@context": {
    "@language": "en",
    "@vocab": "https://schema.org/",
    "citeAs": "cr:citeAs",
    "column": "cr:column",
    "conformsTo": "dct:conformsTo",
    "cr": "http://mlcommons.org/croissant/",
    "rai": "http://mlcommons.org/croissant/RAI/",
    "data": {
      "@id": "cr:data",
      "@type": "@json"
    },
    "dataType": {
      "@id": "cr:dataType",
      "@type": "@vocab"
    },
    "dct": "http://purl.org/dc/terms/",
    "examples": {
      "@id": "cr:examples",
      "@type": "@json"
    },
    "extract": "cr:extract",
    "field": "cr:field",
    "fileProperty": "cr:fileProperty",
    "fileObject": "cr:fileObject",
    "fileSet": "cr:fileSet",
    "format": "cr:format",
    "includes": "cr:includes",
    "isLiveDataset": "cr:isLiveDataset",
    "jsonPath": "cr:jsonPath",
    "key": "cr:key",
    "md5": "cr:md5",
    "parentField": "cr:parentField",
    "path": "cr:path",
    "recordSet": "cr:recordSet",
    "references": "cr:references",
    "regex": "cr:regex",
    "repeated": "cr:repeated",
    "replace": "cr:replace",
    "sc": "https://schema.org/",
    "separator": "cr:separator",
    "source": "cr:source",
    "subField": "cr:subField",
    "transform": "cr:transform"
  },
  "@type": "sc:Dataset",
  "name": "SM3-Text-to-Query",
  "description": "This dataset contains examples of text-to-query mappings for multiple query languages including SQL, SPARQL, MQL, and Cypher. It includes question type and class information.",
  "conformsTo": "http://mlcommons.org/croissant/1.0",
  "citeAs": "SM3-Text-to-Query Dataset",
  "url": "https://github.com/jf87/SM3-Text-to-Query",
  "distribution": [
    {
      "@type": "cr:FileObject",
      "@id": "github-repository",
      "name": "github-repository",
      "description": "Repository hosting the SM3-Text-to-Query dataset.",
      "contentUrl": "https://github.com/jf87/SM3-Text-to-Query",
      "encodingFormat": "git+https",
      "sha256": "main"
    },
    {
      "@type": "cr:FileSet",
      "@id": "csv-files",
      "name": "csv-files",
      "description": "CSV files hosted in the GitHub repository.",
      "containedIn": {
        "@id": "github-repository"
      },
      "encodingFormat": "text/csv",
      "includes": "data/train_dev/*.csv"
    }
  ],
  "recordSet": [
    {
      "@type": "cr:RecordSet",
      "@id": "csv",
      "name": "csv",
      "field": [
        {
          "@type": "cr:Field",
          "@id": "csv/question",
          "name": "question",
          "description": "The natural language question.",
          "dataType": "sc:Text",
          "source": {
            "fileSet": {
              "@id": "csv-files"
            },
            "extract": {
              "column": "question"
            }
          }
        },
        {
          "@type": "cr:Field",
          "@id": "csv/sql",
          "name": "sql",
          "description": "The SQL query.",
          "dataType": "sc:Text",
          "source": {
            "fileSet": {
              "@id": "csv-files"
            },
            "extract": {
              "column": "sql"
            }
          }
        },
        {
          "@type": "cr:Field",
          "@id": "csv/sparql",
          "name": "sparql",
          "description": "The SPARQL query.",
          "dataType": "sc:Text",
          "source": {
            "fileSet": {
              "@id": "csv-files"
            },
            "extract": {
              "column": "sparql"
            }
          }
        },
        {
          "@type": "cr:Field",
          "@id": "csv/mql",
          "name": "mql",
          "description": "The MQL query.",
          "dataType": "sc:Text",
          "source": {
            "fileSet": {
              "@id": "csv-files"
            },
            "extract": {
              "column": "mql"
            }
          }
        },
        {
          "@type": "cr:Field",
          "@id": "csv/cypher",
          "name": "cypher",
          "description": "The Cypher query.",
          "dataType": "sc:Text",
          "source": {
            "fileSet": {
              "@id": "csv-files"
            },
            "extract": {
              "column": "cypher"
            }
          }
        },
        {
          "@type": "cr:Field",
          "@id": "csv/question_type",
          "name": "question_type",
          "description": "The type of the question.",
          "dataType": "sc:Text",
          "source": {
            "fileSet": {
              "@id": "csv-files"
            },
            "extract": {
              "column": "question_type"
            }
          }
        },
        {
          "@type": "cr:Field",
          "@id": "csv/class",
          "name": "class",
          "description": "The class of the query or question.",
          "dataType": "sc:Text",
          "source": {
            "fileSet": {
              "@id": "csv-files"
            },
            "extract": {
              "column": "class"
            }
          }
        }
      ]
    }
  ]
}
```
