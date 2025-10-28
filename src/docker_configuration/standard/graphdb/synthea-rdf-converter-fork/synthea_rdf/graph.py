from pathlib import Path
import copy
from rdflib import Graph
import pandas as pd
from dua import resource as dua_resource
from trustscore import resource as trust_resource
from .resource import (
    Allergy,
    CarePlan,
    Claim,
    ClaimTransaction,
    Condition,
    Device,
    Encounter,
    ImagingStudy,
    Immunization,
    Medication,
    Observation,
    Organization,
    Patient,
    Payer,
    PayerTransition,
    Procedure,
    Provider,
    Supply,
)
from abstract.namespace import SYN, DUA, TST
from alive_progress import alive_bar


def split_dataframe(df: pd.DataFrame, chunk_size: int = 500000) -> list[pd.DataFrame]:
    chunks = list()
    num_chunks = len(df.index) // chunk_size + 1
    print(f"Split dataframe into {num_chunks} chunks.")
    for i in range(num_chunks):
        chunks.append(df[i * chunk_size : (i + 1) * chunk_size])
    print("Chunk sizes:")
    for c in chunks:
        print(len(c.index))
    return chunks


class GraphBuilder:
    def __init__(
        self,
        csv_dir: str,
        model_path: str,
        destination_dir: Path,
        include_dua: bool = False,
        include_trustscore: bool = False,
        skip: list[str] = [],
    ):
        self.RESOURCE_DICT = {
            "allergies.csv": self.convertAllergy,
            "careplans.csv": self.convertCarePlan,
            "claims.csv": self.convertClaim,
            "claims_transactions.csv": self.convertClaimTransaction,
            "conditions.csv": self.convertCondition,
            "devices.csv": self.convertDevice,
            "encounters.csv": self.convertEncounter,
            "imaging_studies.csv": self.convertImagingStudy,
            "immunizations.csv": self.convertImmunization,
            "medications.csv": self.convertMedication,
            "observations.csv": self.convertObservation,
            "organizations.csv": self.convertOrganization,
            "patients.csv": self.convertPatient,
            "payer_transitions.csv": self.convertPayerTransition,
            "payers.csv": self.convertPayer,
            "procedures.csv": self.convertProcedure,
            "providers.csv": self.convertProvider,
            "supplies.csv": self.convertSupply,
        }
        # Optional Trustscore and DUA
        self.include_dua = include_dua
        self.include_trustscore = include_trustscore
        self.skip = skip

        self.graph = Graph()
        self.csv_dir = Path(csv_dir)
        self.destination_dir = destination_dir
        self.setModel(model_path)

    def serialize(self, destination: str):
        return self.graph.serialize(destination=destination)

    def build(self, chunk_size: int = 500000):
        self.convert(chunk_size=chunk_size)
        return self.graph

    def convert(self, chunk_size: int = 500000):
        for file, func in self.RESOURCE_DICT.items():
            if file in self.skip:
                print(f"Skipping {file}")
                continue
            resource_path = Path(self.csv_dir / file)
            if Path(resource_path).exists():
                resource_df = pd.read_csv(resource_path)
                if len(resource_df.index) < chunk_size:
                    func(resource_df)
                    del resource_df
                else:
                    chunks = split_dataframe(resource_df, chunk_size=chunk_size)
                    i = 0
                    for chunk in chunks:
                        print(f"Converting chunk {i}")
                        func(chunk, chunk_id=i)
                        i += 1
                        del chunk
                    del resource_df

        if self.include_dua:
            dua_df = pd.read_csv(self.csv_dir / "dua.csv")
            self.convertDUA(dua_df)

            del dua_df

        if self.include_trustscore:
            trustscore_df = pd.read_csv(self.csv_dir / "trustscore.csv")
            self.convertTrustscore(trustscore_df)

            del trustscore_df

    def setModel(self, model_path):
        self.graph.parse(model_path, format="n3")
        self.graph.bind("syn", SYN)
        if self.include_dua:
            self.graph.bind("dua", DUA)
        if self.include_trustscore:
            self.graph.bind("tst", TST)
        print(f"Model has {len(self.graph)} triples.")

    def convertAllergy(self, allergy_df=None, chunk_id=None):
        graph = copy.deepcopy(self.graph)
        allergy = Allergy(allergy_df)
        allergy.convert(graph)
        with alive_bar(
            title=f"Allergy graph {chunk_id} serialization",
            unknown="waves2",
        ) as bar:
            if chunk_id is not None:
                graph.serialize(
                    destination=self.destination_dir / f"allergy_{chunk_id}.ttl"
                )
            else:
                graph.serialize(destination=self.destination_dir / "allergy.ttl")
            bar()

    def convertCarePlan(self, carePlan_df=None, chunk_id=None):
        graph = copy.deepcopy(self.graph)
        careplan = CarePlan(carePlan_df)
        careplan.convert(graph)
        with alive_bar(
            title=f"Care plan graph {chunk_id} serialization",
            unknown="waves2",
        ) as bar:
            if chunk_id is not None:
                graph.serialize(
                    destination=self.destination_dir / f"careplan_{chunk_id}.ttl"
                )
            else:
                graph.serialize(destination=self.destination_dir / "careplan.ttl")
            bar()

    def convertClaim(self, claim_df=None, chunk_id=None):
        graph = copy.deepcopy(self.graph)
        claim = Claim(claim_df)
        claim.convert(graph)
        with alive_bar(
            title=f"Claim graph {chunk_id} serialization",
            unknown="waves2",
        ) as bar:
            if chunk_id is not None:
                graph.serialize(
                    destination=self.destination_dir / f"claim_{chunk_id}.ttl"
                )
            else:
                graph.serialize(destination=self.destination_dir / "claim.ttl")
            bar()

    def convertClaimTransaction(self, claimTransaction_df=None, chunk_id=None):
        graph = copy.deepcopy(self.graph)
        claimTransaction = ClaimTransaction(claimTransaction_df)
        claimTransaction.convert(graph)
        with alive_bar(
            title=f"Claim transaction graph {chunk_id} serialization",
            unknown="waves2",
        ) as bar:
            if chunk_id is not None:
                graph.serialize(
                    destination=self.destination_dir
                    / f"claim_transaction_{chunk_id}.ttl"
                )
            else:
                graph.serialize(
                    destination=self.destination_dir / "claim_transaction.ttl"
                )
            bar()

    def convertCondition(self, condition_df=None, chunk_id=None):
        graph = copy.deepcopy(self.graph)
        condition = Condition(condition_df)
        condition.convert(graph)
        with alive_bar(
            title=f"Condition graph {chunk_id} serialization",
            unknown="waves2",
        ) as bar:
            if chunk_id is not None:
                graph.serialize(
                    destination=self.destination_dir / f"condition_{chunk_id}.ttl"
                )
            else:
                graph.serialize(destination=self.destination_dir / "condition.ttl")
            bar()

    def convertDevice(self, device_df=None, chunk_id=None):
        graph = copy.deepcopy(self.graph)
        device = Device(device_df)
        device.convert(graph)
        with alive_bar(
            title=f"Device graph {chunk_id} serialization",
            unknown="waves2",
        ) as bar:
            if chunk_id is not None:
                graph.serialize(
                    destination=self.destination_dir / f"device_{chunk_id}.ttl"
                )
            else:
                graph.serialize(destination=self.destination_dir / "device.ttl")
            bar()

    def convertEncounter(self, encounter_df=None, chunk_id=None):
        graph = copy.deepcopy(self.graph)
        encounter = Encounter(encounter_df)
        encounter.convert(graph)
        with alive_bar(
            title=f"Encounter graph {chunk_id} serialization",
            unknown="waves2",
        ) as bar:
            if chunk_id is not None:
                graph.serialize(
                    destination=self.destination_dir / f"encounter_{chunk_id}.ttl"
                )
            else:
                graph.serialize(destination=self.destination_dir / "encounter.ttl")
            bar()

    def convertImagingStudy(self, imagingStudy_df=None, chunk_id=None):
        graph = copy.deepcopy(self.graph)
        imagingStudy = ImagingStudy(imagingStudy_df)
        imagingStudy.convert(graph)
        with alive_bar(
            title=f"Imaging study graph {chunk_id} serialization",
            unknown="waves2",
        ) as bar:
            if chunk_id is not None:
                graph.serialize(
                    destination=self.destination_dir / f"imaging_study_{chunk_id}.ttl"
                )
            else:
                graph.serialize(destination=self.destination_dir / "imaging_study.ttl")
            bar()

    def convertImmunization(self, immunization_df=None, chunk_id=None):
        graph = copy.deepcopy(self.graph)
        immunization = Immunization(immunization_df)
        immunization.convert(graph)
        with alive_bar(
            title=f"Immunization graph {chunk_id} serialization",
            unknown="waves2",
        ) as bar:
            if chunk_id is not None:
                graph.serialize(
                    destination=self.destination_dir / f"immunization_{chunk_id}.ttl"
                )
            else:
                graph.serialize(destination=self.destination_dir / "immunization.ttl")
            bar()

    def convertMedication(self, medication_df=None, chunk_id=None):
        graph = copy.deepcopy(self.graph)
        medication = Medication(medication_df)
        medication.convert(graph)
        with alive_bar(
            title=f"Medication graph {chunk_id} serialization",
            unknown="waves2",
        ) as bar:
            if chunk_id is not None:
                graph.serialize(
                    destination=self.destination_dir / f"medication_{chunk_id}.ttl"
                )
            else:
                graph.serialize(destination=self.destination_dir / "medication.ttl")
            bar()

    def convertObservation(self, observation_df=None, chunk_id=None):
        graph = copy.deepcopy(self.graph)
        observation = Observation(observation_df)
        observation.convert(graph)
        with alive_bar(
            title=f"Observation graph {chunk_id} serialization",
            unknown="waves2",
        ) as bar:
            if chunk_id is not None:
                graph.serialize(
                    destination=self.destination_dir / f"observation_{chunk_id}.ttl"
                )
            else:
                graph.serialize(destination=self.destination_dir / "observation.ttl")
            bar()

    def convertOrganization(self, organization_df=None, chunk_id=None):
        graph = copy.deepcopy(self.graph)
        organization = Organization(organization_df)
        organization.convert(graph)
        with alive_bar(
            title=f"Organization graph {chunk_id} serialization",
            unknown="waves2",
        ) as bar:
            if chunk_id is not None:
                graph.serialize(
                    destination=self.destination_dir / f"organization_{chunk_id}.ttl"
                )
            else:
                graph.serialize(destination=self.destination_dir / "organization.ttl")
            bar()

    def convertPatient(self, patient_df=None, chunk_id=None):
        graph = copy.deepcopy(self.graph)
        patient = Patient(patient_df)
        patient.convert(graph)
        with alive_bar(
            title=f"Patient graph {chunk_id} serialization",
            unknown="waves2",
        ) as bar:
            if chunk_id is not None:
                graph.serialize(
                    destination=self.destination_dir / f"patient_{chunk_id}.ttl"
                )
            else:
                graph.serialize(destination=self.destination_dir / "patient.ttl")
            bar()

    def convertPayer(self, payer_df=None, chunk_id=None):
        graph = copy.deepcopy(self.graph)
        payer = Payer(payer_df)
        payer.convert(graph)
        with alive_bar(
            title=f"Payer graph {chunk_id} serialization",
            unknown="waves2",
        ) as bar:
            if chunk_id is not None:
                graph.serialize(
                    destination=self.destination_dir / f"payer_{chunk_id}.ttl"
                )
            else:
                graph.serialize(destination=self.destination_dir / "payer.ttl")
            bar()

    def convertPayerTransition(self, payerTransition_df=None, chunk_id=None):
        graph = copy.deepcopy(self.graph)
        payerTransition = PayerTransition(payerTransition_df)
        payerTransition.convert(graph)
        with alive_bar(
            title=f"Payer transition graph {chunk_id} serialization",
            unknown="waves2",
        ) as bar:
            if chunk_id is not None:
                graph.serialize(
                    destination=self.destination_dir
                    / f"payer_transition_{chunk_id}.ttl"
                )
            else:
                graph.serialize(
                    destination=self.destination_dir / "payer_transition.ttl"
                )
            bar()

    def convertProcedure(self, procedure_df=None, chunk_id=None):
        graph = copy.deepcopy(self.graph)
        procedure = Procedure(procedure_df)
        procedure.convert(graph)
        with alive_bar(
            title=f"Procedure graph {chunk_id} serialization",
            unknown="waves2",
        ) as bar:
            if chunk_id is not None:
                graph.serialize(
                    destination=self.destination_dir / f"procedure_{chunk_id}.ttl"
                )
            else:
                graph.serialize(destination=self.destination_dir / "procedure.ttl")
            bar()

    def convertProvider(self, provider_df=None, chunk_id=None):
        graph = copy.deepcopy(self.graph)
        provider = Provider(provider_df)
        provider.convert(graph)
        with alive_bar(
            title=f"Provider graph {chunk_id} serialization",
            unknown="waves2",
        ) as bar:
            if chunk_id is not None:
                graph.serialize(
                    destination=self.destination_dir / f"provider_{chunk_id}.ttl"
                )
            else:
                graph.serialize(destination=self.destination_dir / "provider.ttl")
            bar()

    def convertSupply(self, supply_df=None, chunk_id=None):
        graph = copy.deepcopy(self.graph)
        supply = Supply(supply_df)
        supply.convert(graph)
        with alive_bar(
            title=f"Supply graph {chunk_id} serialization",
            unknown="waves2",
        ) as bar:
            if chunk_id is not None:
                graph.serialize(
                    destination=self.destination_dir / f"supply_{chunk_id}.ttl"
                )
            else:
                graph.serialize(destination=self.destination_dir / "supply.ttl")
            bar()

    def convertDUA(self, dua_df=None):
        graph = copy.deepcopy(self.graph)
        dua = dua_resource.DataUsageAgreement(dua_df)
        dua.convert(graph)
        with alive_bar(
            title="DUA graph Serialization",
            unknown="waves2",
        ) as bar:
            graph.serialize(destination=self.destination_dir / "dua.ttl")
            bar()

    def convertTrustscore(self, trustscore_df=None):
        graph = copy.deepcopy(self.graph)
        trustscore = trust_resource.TrustScore(trustscore_df)
        trustscore.convert(graph)
        with alive_bar(
            title="Trust score graph Serialization",
            unknown="waves2",
        ) as bar:
            graph.serialize(destination=self.destination_dir / "trustscore.ttl")
            bar()

    # def convertCarePlan(self, carePlan_df=None):
    #     careplan = CarePlan(carePlan_df)
    #     careplan.convert(self.graph)

    # def convertClaim(self, claim_df=None):
    #     claim = Claim(claim_df)
    #     claim.convert(self.graph)

    # def convertClaimTransaction(self, claimTransaction_df=None):
    #     claimTransaction = ClaimTransaction(claimTransaction_df)
    #     claimTransaction.convert(self.graph)

    # def convertCondition(self, condition_df=None):
    #     condition = Condition(condition_df)
    #     condition.convert(self.graph)

    # def convertDevice(self, device_df=None):
    #     device = Device(device_df)
    #     device.convert(self.graph)

    # def convertEncounter(self, encounter_df=None):
    #     encounter = Encounter(encounter_df)
    #     encounter.convert(self.graph)

    # def convertImagingStudy(self, imagingStudy_df=None):
    #     imagingStudy = ImagingStudy(imagingStudy_df)
    #     imagingStudy.convert(self.graph)

    # def convertImmunization(self, immunization_df=None):
    #     immunization = Immunization(immunization_df)
    #     immunization.convert(self.graph)

    # def convertMedication(self, medication_df=None):
    #     medication = Medication(medication_df)
    #     medication.convert(self.graph)

    # def convertObservation(self, observation_df=None):
    #     observation = Observation(observation_df)
    #     observation.convert(self.graph)

    # def convertOrganization(self, organization_df=None):
    #     organization = Organization(organization_df)
    #     organization.convert(self.graph)

    # def convertPatient(self, patient_df=None):
    #     patient = Patient(patient_df)
    #     patient.convert(self.graph)

    # def convertPayer(self, payer_df=None):
    #     payer = Payer(payer_df)
    #     payer.convert(self.graph)

    # def convertPayerTransition(self, payerTransition_df=None):
    #     payerTransition = PayerTransition(payerTransition_df)
    #     payerTransition.convert(self.graph)

    # def convertProcedure(self, procedure_df=None):
    #     procedure = Procedure(procedure_df)
    #     procedure.convert(self.graph)

    # def convertProvider(self, provider_df=None):
    #     provider = Provider(provider_df)
    #     provider.convert(self.graph)

    # def convertSupply(self, supply_df=None):
    #     supply = Supply(supply_df)
    #     supply.convert(self.graph)

    # def convertDUA(self, dua_df):
    #     dua = dua_resource.DataUsageAgreement(dua_df)
    #     dua.convert(self.graph)

    # def convertTrustscore(self, trustscore_df):
    #     trust = trust_resource.TrustScore(trustscore_df)
    #     trust.convert(self.graph)
