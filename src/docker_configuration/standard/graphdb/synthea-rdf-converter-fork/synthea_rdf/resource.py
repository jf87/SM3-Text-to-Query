from rdflib.namespace import RDF
from alive_progress import alive_bar
import pandas as pd
from abstract import Resource
from abstract.namespace import SYN
from abstract.literal import (
    dateLiteral,
    dateTimeLiteral,
    dicomUidLiteral,
    dicomDcmLiteral,
    dicomSopLiteral,
    fdaUdiLiteral,
    floatLiteral,
    hl7CvxLiteral,
    integerLiteral,
    loincLiteral,
    plainLiteral,
    snomedCtLiteral,
    umlsRxnormLiteral,
    urnUuidLiteral,
)
from abstract.uri import (
    allergyUri,
    carePlanUri,
    claimUri,
    claimTransactionUri,
    conditionUri,
    deviceUri,
    encounterUri,
    imagingStudyUri,
    immunizationUri,
    medicationUri,
    observationUri,
    organizationUri,
    patientUri,
    payerUri,
    payertransitionUri,
    procedureUri,
    providerUri,
    supplyUri,
)

# from .trust import generate_user_trust, generate_org_trust, generate_veracity


"""
Issue:
    - [ ] Confusing naming convention for the following data properties:
        - syn:start
        - syn:startDate
        - syn:startDateTime
        - syn:date
        - syn:dateTime
"""


class Allergy(Resource):
    def __init__(self, df):
        self.__resource_df = df

    @property
    def resource_df(self):
        return self.__resource_df

    @resource_df.setter
    def resource_df(self, value):
        self.__resource_df = value

    def convert(self, graph):
        """
        Issue:
            - [ ] There are no allergy data in the dataset (10 patients)
                  so I should test this conversion with a larger dataset.
            - [ ] syn:code should be decided by the syn:system
        """
        rows = self.__resource_df.shape[0]
        with alive_bar(rows, force_tty=True, title="Allergy Conversion") as bar:
            for index, row in self.__resource_df.iterrows():
                # Create name of the allergy class individual
                allergy = allergyUri(index)
                patient = patientUri(row["PATIENT"])
                encounter = encounterUri(row["ENCOUNTER"])

                # Data Properties
                graph.add((allergy, RDF.type, SYN.Allergy))
                graph.add((allergy, SYN.startDate, dateLiteral(row["START"])))
                graph.add((allergy, SYN.patientId, urnUuidLiteral(row["PATIENT"])))
                graph.add((allergy, SYN.encounterId, urnUuidLiteral(row["ENCOUNTER"])))
                graph.add((allergy, SYN.system, plainLiteral(row["SYSTEM"])))
                graph.add((allergy, SYN.description, plainLiteral(row["DESCRIPTION"])))
                graph.add((allergy, SYN.code, snomedCtLiteral(row["CODE"])))
                graph.add((allergy, SYN.category, snomedCtLiteral(row["CATEGORY"])))

                # Object Properties
                graph.add((allergy, SYN.isAbout, patient))
                graph.add((patient, SYN.hasAllergy, allergy))
                graph.add((allergy, SYN.isDiagnosedDuring, encounter))
                graph.add((encounter, SYN.hasDiagnosed, allergy))

                # Check if REACTION1 column is not empty
                if pd.notna(row["REACTION1"]):
                    graph.add((allergy, SYN.hasReaction1, plainLiteral(row["REACTION1"])))
                    graph.add((allergy, SYN.description1, plainLiteral(row["DESCRIPTION1"])))
                    graph.add((allergy, SYN.severity, plainLiteral(row["SEVERITY1"])))

                # Check if REACTION2 column is not empty
                if pd.notna(row["REACTION2"]):
                    graph.add((allergy, SYN.hasReaction2, plainLiteral(row["REACTION2"])))
                    graph.add((allergy, SYN.description2, plainLiteral(row["DESCRIPTION2"])))
                    graph.add((allergy, SYN.severity, plainLiteral(row["SEVERITY2"])))
                
                if pd.notna(row["STOP"]):
                    graph.add((allergy, SYN.endDate, dateLiteral(row["STOP"])))

                if pd.notna(row["TYPE"]):
                    graph.add((allergy, SYN.type, plainLiteral(row["TYPE"])))
                bar()


class CarePlan(Resource):
    def __init__(self, df):
        self.__resource_df = df

    @property
    def resource_df(self):
        return self.__resource_df

    @resource_df.setter
    def resource_df(self, value):
        self.__resource_df = value

    def convert(self, graph):
        rows = self.__resource_df.shape[0]
        with alive_bar(rows, force_tty=True, title="CarePlan Conversion") as bar:
            for index, row in self.__resource_df.iterrows():
                # Create name of the careplan class individual
                careplan = carePlanUri(row["Id"])
                patient = patientUri(row["PATIENT"])
                encounter = encounterUri(row["ENCOUNTER"])

                # Data Properties
                graph.add((careplan, RDF.type, SYN.CarePlan))
                graph.add((careplan, SYN.start, dateLiteral(row["START"])))
                graph.add((careplan, SYN.patientId, urnUuidLiteral(row["PATIENT"])))
                graph.add((careplan, SYN.encounterId, urnUuidLiteral(row["ENCOUNTER"])))
                graph.add((careplan, SYN.code, snomedCtLiteral(row["CODE"])))
                graph.add((careplan, SYN.description, plainLiteral(row["DESCRIPTION"])))
                graph.add(
                    (careplan, SYN.reasonCode, snomedCtLiteral(row["REASONCODE"]))
                )
                graph.add(
                    (
                        careplan,
                        SYN.reasonDescription,
                        plainLiteral(row["REASONDESCRIPTION"]),
                    )
                )

                # Object Properties
                graph.add((careplan, SYN.isAbout, patient))
                graph.add((patient, SYN.hasCarePlan, careplan))
                graph.add((careplan, SYN.isOrderedDuring, encounter))
                graph.add((encounter, SYN.hasOrdered, careplan))

                bar()


class Claim(Resource):
    def __init__(self, df):
        self.__resource_df = df

    @property
    def resource_df(self):
        return self.__resource_df

    @resource_df.setter
    def resource_df(self, value):
        self.__resource_df = value

    def convert(self, graph):
        """
        Object properties covered by other resource conversion:
            - [x] syn:Claim syn:hasTransaction syn:ClaimTransaction
        """
        rows = self.__resource_df.shape[0]
        with alive_bar(rows, force_tty=True, title="Claim Conversion") as bar:
            for index, row in self.__resource_df.iterrows():
                # Create name of the claim class individual
                claim = claimUri(row["Id"])
                patient = patientUri(row["PATIENTID"])
                provider = providerUri(row["PROVIDERID"])

                # Data Properties
                graph.add((claim, RDF.type, SYN.Claim))
                graph.add((claim, SYN.id, urnUuidLiteral(row["Id"])))
                graph.add((claim, SYN.patientId, urnUuidLiteral(row["PATIENTID"])))
                graph.add((claim, SYN.providerId, urnUuidLiteral(row["PROVIDERID"])))
                graph.add(
                    (claim, SYN.departmentId, urnUuidLiteral(row["DEPARTMENTID"]))
                )
                graph.add(
                    (
                        claim,
                        SYN.patientDepartmentId,
                        urnUuidLiteral(row["PATIENTDEPARTMENTID"]),
                    )
                )
                graph.add(
                    (
                        claim,
                        SYN.diagnosis1,
                        snomedCtLiteral(row["DIAGNOSIS1"]),
                    )
                )
                graph.add(
                    (
                        claim,
                        SYN.diagnosis2,
                        snomedCtLiteral(row["DIAGNOSIS2"]),
                    )
                )
                graph.add(
                    (
                        claim,
                        SYN.diagnosis3,
                        snomedCtLiteral(row["DIAGNOSIS3"]),
                    )
                )
                graph.add(
                    (
                        claim,
                        SYN.diagnosis4,
                        snomedCtLiteral(row["DIAGNOSIS4"]),
                    )
                )
                graph.add(
                    (
                        claim,
                        SYN.diagnosis5,
                        snomedCtLiteral(row["DIAGNOSIS5"]),
                    )
                )
                graph.add(
                    (
                        claim,
                        SYN.diagnosis6,
                        snomedCtLiteral(row["DIAGNOSIS6"]),
                    )
                )
                graph.add(
                    (
                        claim,
                        SYN.diagnosis7,
                        snomedCtLiteral(row["DIAGNOSIS7"]),
                    )
                )
                graph.add(
                    (
                        claim,
                        SYN.diagnosis8,
                        snomedCtLiteral(row["DIAGNOSIS8"]),
                    )
                )
                graph.add(
                    (
                        claim,
                        SYN.currentIllnessDate,
                        dateTimeLiteral(row["CURRENTILLNESSDATE"]),
                    )
                )
                graph.add((claim, SYN.serviceDate, dateTimeLiteral(row["SERVICEDATE"])))

                # Object Properties
                graph.add((claim, SYN.isAssociatedWith, patient))
                graph.add((patient, SYN.hasClaim, claim))
                graph.add((claim, SYN.isFiledBy, provider))
                graph.add((provider, SYN.hasFiled, claim))

                bar()


class ClaimTransaction(Resource):
    def __init__(self, df):
        self.__resource_df = df

    @property
    def resource_df(self):
        return self.__resource_df

    @resource_df.setter
    def resource_df(self, value):
        self.__resource_df = value

    def convert(self, graph):
        rows = self.__resource_df.shape[0]
        with alive_bar(
            rows, force_tty=True, title="ClaimTransaction Conversion"
        ) as bar:
            for index, row in self.__resource_df.iterrows():
                # Create name of the claimtransaction class individual
                claimtransaction = claimTransactionUri(row["ID"])
                claim = claimUri(row["CLAIMID"])
                patient = patientUri(row["PATIENTID"])
                provider = providerUri(row["PROVIDERID"])
                organization = organizationUri(row["PLACEOFSERVICE"])

                # Data Properties
                graph.add((claimtransaction, RDF.type, SYN.ClaimTransaction))
                graph.add((claimtransaction, SYN.id, urnUuidLiteral(row["ID"])))
                graph.add((claimtransaction, SYN.amount, floatLiteral(row["AMOUNT"])))
                graph.add(
                    (claimtransaction, SYN.claimId, urnUuidLiteral(row["CLAIMID"]))
                )
                graph.add(
                    (claimtransaction, SYN.chargeId, urnUuidLiteral(row["CHARGEID"]))
                )
                graph.add(
                    (claimtransaction, SYN.patientId, urnUuidLiteral(row["PATIENTID"]))
                )
                graph.add((claimtransaction, SYN.type, plainLiteral(row["TYPE"])))
                graph.add(
                    (
                        claimtransaction,
                        SYN.placeOfService,
                        urnUuidLiteral(row["PLACEOFSERVICE"]),
                    )
                )
                graph.add(
                    (
                        claimtransaction,
                        SYN.procedureCode,
                        snomedCtLiteral(row["PROCEDURECODE"]),
                    )
                )
                graph.add(
                    (
                        claimtransaction,
                        SYN.providerId,
                        urnUuidLiteral(row["PROVIDERID"]),
                    )
                )

                # Object Properties
                graph.add((claimtransaction, SYN.isTransactionFor, claim))
                graph.add((claim, SYN.hasTransaction, claimtransaction))
                graph.add((claimtransaction, SYN.isAssociatedWith, patient))
                graph.add((patient, SYN.hasClaimTransaction, claimtransaction))
                graph.add((claimtransaction, SYN.isAssociatedWith, provider))
                graph.add((provider, SYN.hasClaimTransaction, claimtransaction))
                graph.add((claimtransaction, SYN.hasPlaceOfService, organization))
                graph.add((organization, SYN.hasClaimTransaction, claimtransaction))

                bar()


class Condition(Resource):
    def __init__(self, df):
        self.__resource_df = df

    @property
    def resource_df(self):
        return self.__resource_df

    @resource_df.setter
    def resource_df(self, value):
        self.__resource_df = value

    def convert(self, graph):
        rows = self.__resource_df.shape[0]
        with alive_bar(rows, force_tty=True, title="Condition Conversion") as bar:
            for index, row in self.__resource_df.iterrows():
                # Create name of the condition class individual
                condition = conditionUri(index)
                patient = patientUri(row["PATIENT"])
                encounter = encounterUri(row["ENCOUNTER"])

                # Data Properties
                graph.add((condition, RDF.type, SYN.Condition))
                graph.add((condition, SYN.startDate, dateLiteral(row["START"])))
                if pd.notna(row["STOP"]):
                    graph.add((condition, SYN.endDateTime, dateLiteral(row["STOP"])))
                graph.add((condition, SYN.patientId, urnUuidLiteral(row["PATIENT"])))
                graph.add(
                    (condition, SYN.encounterId, urnUuidLiteral(row["ENCOUNTER"]))
                )
                graph.add((condition, SYN.code, snomedCtLiteral(row["CODE"])))
                graph.add(
                    (condition, SYN.description, plainLiteral(row["DESCRIPTION"]))
                )

                # Object Properties
                graph.add((condition, SYN.isAbout, patient))
                graph.add((patient, SYN.hasHistoryOf, condition))
                graph.add((condition, SYN.isDiagnosedDuring, encounter))
                graph.add((encounter, SYN.hasDiagnosed, condition))

                bar()


class Device(Resource):
    def __init__(self, df):
        self.__resource_df = df

    @property
    def resource_df(self):
        return self.__resource_df

    @resource_df.setter
    def resource_df(self, value):
        self.__resource_df = value

    def convert(self, graph):
        rows = self.__resource_df.shape[0]
        with alive_bar(rows, force_tty=True, title="Device Conversion") as bar:
            for index, row in self.__resource_df.iterrows():
                # Create name of the device class individual
                device = deviceUri(index)
                patient = patientUri(row["PATIENT"])
                encounter = encounterUri(row["ENCOUNTER"])

                # Data Properties
                graph.add((device, RDF.type, SYN.Device))
                graph.add((device, SYN.startDateTime, dateTimeLiteral(row["START"])))
                graph.add((device, SYN.patientId, urnUuidLiteral(row["PATIENT"])))
                graph.add((device, SYN.encounterId, urnUuidLiteral(row["ENCOUNTER"])))
                graph.add((device, SYN.code, snomedCtLiteral(row["CODE"])))
                graph.add((device, SYN.description, plainLiteral(row["DESCRIPTION"])))
                graph.add((device, SYN.udi, fdaUdiLiteral(row["UDI"])))

                # Object Properties
                graph.add((device, SYN.hasMeasured, patient))
                graph.add((patient, SYN.isMeasuredBy, device))
                graph.add((device, SYN.isOrderedDuring, encounter))
                graph.add((encounter, SYN.hasOrdered, device))

                bar()


class Encounter(Resource):
    def __init__(self, df):
        self.__resource_df = df

    @property
    def resource_df(self):
        return self.__resource_df

    @resource_df.setter
    def resource_df(self, value):
        self.__resource_df = value

    def convert(self, graph):
        rows = self.__resource_df.shape[0]
        # veracity = generate_veracity(rows)
        with alive_bar(rows, force_tty=True, title="Encounter Conversion") as bar:
            for index, row in self.__resource_df.iterrows():
                # Create name of the encounter class individual
                encounter = encounterUri(row["Id"])
                organization = organizationUri(row["ORGANIZATION"])
                patient = patientUri(row["PATIENT"])
                provider = providerUri(row["PROVIDER"])
                payer = payerUri(row["PAYER"])

                # Data Properties
                graph.add((encounter, RDF.type, SYN.Encounter))
                graph.add((encounter, SYN.id, urnUuidLiteral(row["Id"])))
                graph.add((encounter, SYN.startDateTime, dateTimeLiteral(row["START"])))
                graph.add((encounter, SYN.patientId, urnUuidLiteral(row["PATIENT"])))
                graph.add(
                    (encounter, SYN.organizationId, urnUuidLiteral(row["ORGANIZATION"]))
                )
                graph.add((encounter, SYN.providerId, urnUuidLiteral(row["PROVIDER"])))
                graph.add((encounter, SYN.payerId, urnUuidLiteral(row["PAYER"])))
                graph.add(
                    (encounter, SYN.encounterClass, plainLiteral(row["ENCOUNTERCLASS"]))
                )
                graph.add((encounter, SYN.code, snomedCtLiteral(row["CODE"])))
                graph.add(
                    (encounter, SYN.description, plainLiteral(row["DESCRIPTION"]))
                )
                graph.add(
                    (
                        encounter,
                        SYN.baseEncounterCost,
                        floatLiteral(row["BASE_ENCOUNTER_COST"]),
                    )
                )
                graph.add(
                    (
                        encounter,
                        SYN.totalClaimCost,
                        floatLiteral(row["TOTAL_CLAIM_COST"]),
                    )
                )
                graph.add(
                    (encounter, SYN.payerCoverage, floatLiteral(row["PAYER_COVERAGE"]))
                )

                # Object Properties
                graph.add((encounter, SYN.hasPatient, patient))
                graph.add((encounter, SYN.isPerformedAt, organization))
                graph.add((encounter, SYN.isPerformedBy, provider))
                graph.add((provider, SYN.hasPerformed, encounter))
                graph.add((encounter, SYN.isCoveredBy, payer))

                graph.add(
                    (encounter, SYN.reasonCode, snomedCtLiteral(row["REASONCODE"]))
                )
                graph.add(
                    (
                        encounter,
                        SYN.reasonDescription,
                        plainLiteral(row["REASONDESCRIPTION"]),
                    )
                )

                bar()


class ImagingStudy(Resource):
    def __init__(self, df):
        self.__resource_df = df

    @property
    def resource_df(self):
        return self.__resource_df

    @resource_df.setter
    def resource_df(self, value):
        self.__resource_df = value

    def convert(self, graph):
        """
        Issue:
            - [ ] There are no ImagingStudy data in the dataset (10 patients)
                  so I should test this conversion with a larger dataset.
        """
        rows = self.__resource_df.shape[0]
        with alive_bar(rows, force_tty=True, title="ImagingStudy Conversion") as bar:
            for index, row in self.__resource_df.iterrows():
                # Create name of the imagingstudy class individual
                imagingstudy = imagingStudyUri(index)
                patient = patientUri(row["PATIENT"])
                encounter = encounterUri(row["ENCOUNTER"])

                # Data Properties
                graph.add((imagingstudy, RDF.type, SYN.ImagingStudy))
                graph.add((imagingstudy, SYN.id, urnUuidLiteral(row["Id"])))
                graph.add((imagingstudy, SYN.dateTime, dateTimeLiteral(row["DATE"])))
                graph.add((imagingstudy, SYN.patientId, urnUuidLiteral(row["PATIENT"])))
                graph.add(
                    (imagingstudy, SYN.encounterId, urnUuidLiteral(row["ENCOUNTER"]))
                )
                graph.add(
                    (imagingstudy, SYN.seriesUid, dicomUidLiteral(row["SERIES_UID"]))
                )
                graph.add(
                    (
                        imagingstudy,
                        SYN.bodySiteCode,
                        snomedCtLiteral(row["BODYSITE_CODE"]),
                    )
                )
                graph.add(
                    (
                        imagingstudy,
                        SYN.bodySiteDescription,
                        plainLiteral(row["BODYSITE_DESCRIPTION"]),
                    )
                )
                graph.add(
                    (
                        imagingstudy,
                        SYN.modalityCode,
                        dicomDcmLiteral(row["MODALITY_CODE"]),
                    )
                )
                graph.add(
                    (
                        imagingstudy,
                        SYN.modalityDescription,
                        plainLiteral(row["MODALITY_DESCRIPTION"]),
                    )
                )
                graph.add(
                    (
                        imagingstudy,
                        SYN.instanceUid,
                        dicomUidLiteral(row["INSTANCE_UID"]),
                    )
                )
                graph.add((imagingstudy, SYN.sopCode, dicomSopLiteral(row["SOP_CODE"])))
                graph.add(
                    (
                        imagingstudy,
                        SYN.sopDescription,
                        plainLiteral(row["SOP_DESCRIPTION"]),
                    )
                )
                graph.add(
                    (
                        imagingstudy,
                        SYN.procedureCode,
                        snomedCtLiteral(row["PROCEDURE_CODE"]),
                    )
                )

                # Object Properties
                graph.add((imagingstudy, SYN.isAbout, patient))
                graph.add((patient, SYN.hasHistoryOf, imagingstudy))
                graph.add((imagingstudy, SYN.isOrderedDuring, encounter))
                graph.add((encounter, SYN.hasOrdered, imagingstudy))

                bar()


class Immunization(Resource):
    def __init__(self, df):
        self.__resource_df = df

    @property
    def resource_df(self):
        return self.__resource_df

    @resource_df.setter
    def resource_df(self, value):
        self.__resource_df = value

    def convert(self, graph):
        rows = self.__resource_df.shape[0]
        with alive_bar(rows, force_tty=True, title="Immunization Conversion") as bar:
            for index, row in self.__resource_df.iterrows():
                # Create name of the immunization class individual
                immunization = immunizationUri(index)
                patient = patientUri(row["PATIENT"])
                encounter = encounterUri(row["ENCOUNTER"])

                # Data Properties
                graph.add((immunization, RDF.type, SYN.Immunization))
                graph.add((immunization, SYN.dateTime, dateTimeLiteral(row["DATE"])))
                graph.add((immunization, SYN.patientId, urnUuidLiteral(row["PATIENT"])))
                graph.add(
                    (immunization, SYN.encounterId, urnUuidLiteral(row["ENCOUNTER"]))
                )
                graph.add((immunization, SYN.code, hl7CvxLiteral(row["CODE"])))
                graph.add(
                    (immunization, SYN.description, plainLiteral(row["DESCRIPTION"]))
                )
                graph.add((immunization, SYN.cost, floatLiteral(row["BASE_COST"])))

                # Object Properties
                graph.add((immunization, SYN.isPrescribedFor, patient))
                graph.add((patient, SYN.hasHistoryOf, immunization))
                graph.add((immunization, SYN.isPrescribedDuring, encounter))
                graph.add((encounter, SYN.hasPrescribed, immunization))

                bar()


class Medication(Resource):
    def __init__(self, df):
        self.__resource_df = df

    @property
    def resource_df(self):
        return self.__resource_df

    @resource_df.setter
    def resource_df(self, value):
        self.__resource_df = value

    def convert(self, graph):
        rows = self.__resource_df.shape[0]
        with alive_bar(rows, force_tty=True, title="Medication Conversion") as bar:
            for index, row in self.__resource_df.iterrows():
                # Create name of the medication class individual
                medication = medicationUri(index)
                patient = patientUri(row["PATIENT"])
                encounter = encounterUri(row["ENCOUNTER"])
                payer = payerUri(row["PAYER"])

                # Data Properties
                graph.add((medication, RDF.type, SYN.Medication))
                graph.add(
                    (medication, SYN.startDateTime, dateTimeLiteral(row["START"]))
                )
                graph.add((medication, SYN.patientId, urnUuidLiteral(row["PATIENT"])))
                graph.add((medication, SYN.payerId, urnUuidLiteral(row["PAYER"])))
                graph.add(
                    (medication, SYN.encounterId, urnUuidLiteral(row["ENCOUNTER"]))
                )
                graph.add((medication, SYN.code, umlsRxnormLiteral(row["CODE"])))
                graph.add(
                    (medication, SYN.description, plainLiteral(row["DESCRIPTION"]))
                )
                graph.add((medication, SYN.baseCost, floatLiteral(row["BASE_COST"])))
                graph.add(
                    (medication, SYN.payerCoverage, floatLiteral(row["PAYER_COVERAGE"]))
                )
                graph.add((medication, SYN.dispense, floatLiteral(row["DISPENSES"])))
                graph.add((medication, SYN.totalCost, floatLiteral(row["TOTALCOST"])))

                # Object Properties
                graph.add((medication, SYN.isPrescribedFor, patient))
                graph.add((patient, SYN.hasHistoryOf, medication))
                graph.add((medication, SYN.isPrescribedDuring, encounter))
                graph.add((encounter, SYN.hasPrescribed, medication))
                graph.add((payer, SYN.hasCovered, medication))
                graph.add((medication, SYN.isCoveredBy, payer))

                bar()


class Observation(Resource):
    def __init__(self, df):
        self.__resource_df = df

    @property
    def resource_df(self):
        return self.__resource_df

    @resource_df.setter
    def resource_df(self, value):
        self.__resource_df = value

    def convert(self, graph):
        rows = self.__resource_df.shape[0]
        # veracity = generate_veracity(rows)
        with alive_bar(rows, force_tty=True, title="Obvervation Conversion") as bar:
            for index, row in self.__resource_df.iterrows():
                # Create name of the observation class individual
                observation = observationUri(index)

                # Data Properties
                graph.add((observation, RDF.type, SYN.Observation))
                graph.add((observation, SYN.dateTime, dateTimeLiteral(row["DATE"])))
                graph.add((observation, SYN.patientId, urnUuidLiteral(row["PATIENT"])))
                if pd.notnull(row["ENCOUNTER"]):
                    graph.add(
                        (observation, SYN.encounterId, urnUuidLiteral(row["ENCOUNTER"]))
                    )
                graph.add((observation, SYN.code, loincLiteral(row["CODE"])))
                graph.add(
                    (observation, SYN.description, plainLiteral(row["DESCRIPTION"]))
                )
                graph.add((observation, SYN.value, plainLiteral(row["VALUE"])))
                graph.add((observation, SYN.type, plainLiteral(row["TYPE"])))

                # Object Properties
                if pd.notnull(row["ENCOUNTER"]):
                    graph.add(
                        (
                            observation,
                            SYN.isOrderedDuring,
                            encounterUri(row["ENCOUNTER"]),
                        )
                    )
                graph.add((observation, SYN.isAbout, patientUri(row["PATIENT"])))

                bar()


class Organization(Resource):
    # This class use TRUST_IRI for now.
    def __init__(self, df):
        self.__resource_df = df

    @property
    def resource_df(self):
        return self.__resource_df

    @resource_df.setter
    def resource_df(self, value):
        self.__resource_df = value

    def convert(self, graph):
        """
        Object properties covered by other resource conversion:
            - [x] syn:Organization syn:hasClaimTransaction syn:ClaimTransaction
            - [ ] syn:Organization syn:isResponsibleFor syn:Encounter
            - [x] syn:Organization syn:hasEmployed syn:Provider
        """
        rows = self.__resource_df.shape[0]
        # reputation = generate_org_trust(rows)
        with alive_bar(rows, force_tty=True, title="Organization Conversion") as bar:
            for index, row in self.__resource_df.iterrows():
                # Create name of the organization class individual
                organization = organizationUri(row["Id"])

                # Data Properties
                graph.add((organization, RDF.type, SYN.Organization))
                graph.add((organization, SYN.id, urnUuidLiteral(row["Id"])))
                graph.add((organization, SYN.name, plainLiteral(row["NAME"])))
                graph.add((organization, SYN.address, plainLiteral(row["ADDRESS"])))
                graph.add((organization, SYN.city, plainLiteral(row["CITY"])))
                graph.add((organization, SYN.revenue, floatLiteral(row["REVENUE"])))
                graph.add(
                    (organization, SYN.utilization, integerLiteral(row["UTILIZATION"]))
                )

                bar()


class Patient(Resource):
    def __init__(self, df):
        self.__resource_df = df

    @property
    def resource_df(self):
        return self.__resource_df

    @resource_df.setter
    def resource_df(self, value):
        self.__resource_df = value

    def convert(self, graph):
        rows = self.__resource_df.shape[0]
        # user_trust = generate_user_trust(rows)
        with alive_bar(rows, force_tty=True, title="Patient Conversion") as bar:
            for index, row in self.__resource_df.iterrows():
                # Create name of the patient class individual
                patient = patientUri(row["Id"])

                # Data Properties
                graph.add((patient, RDF.type, SYN.Patient))  # type
                graph.add((patient, SYN.id, urnUuidLiteral(row["Id"])))  # id
                graph.add(
                    (patient, SYN.birthdate, dateLiteral(row["BIRTHDATE"]))
                )  # birthdate
                graph.add((patient, SYN.ssn, plainLiteral(row["SSN"])))  # ssn
                graph.add((patient, SYN.first, plainLiteral(row["FIRST"])))
                graph.add((patient, SYN.last, plainLiteral(row["LAST"])))
                graph.add((patient, SYN.race, plainLiteral(row["RACE"])))
                graph.add((patient, SYN.ethnicity, plainLiteral(row["ETHNICITY"])))
                graph.add((patient, SYN.gender, plainLiteral(row["GENDER"])))
                graph.add((patient, SYN.birthplace, plainLiteral(row["BIRTHPLACE"])))
                graph.add((patient, SYN.address, plainLiteral(row["ADDRESS"])))
                graph.add((patient, SYN.city, plainLiteral(row["CITY"])))
                graph.add((patient, SYN.state, plainLiteral(row["STATE"])))

                if pd.notna(row["COUNTY"]):
                    graph.add((patient, SYN.county, plainLiteral(row["COUNTY"])))
                graph.add(
                    (
                        patient,
                        SYN.healthcareExpense,
                        plainLiteral(row["HEALTHCARE_EXPENSES"]),
                    )
                )
                graph.add(
                    (
                        patient,
                        SYN.healthcareCoverage,
                        plainLiteral(row["HEALTHCARE_COVERAGE"]),
                    )
                )
                graph.add((patient, SYN.income, integerLiteral(row["INCOME"])))

                bar()


class Payer(Resource):
    def __init__(self, df):
        self.__resource_df = df

    @property
    def resource_df(self):
        return self.__resource_df

    @resource_df.setter
    def resource_df(self, value):
        self.__resource_df = value

    def convert(self, graph):
        """
        Object properties covered by other resource conversion:
            - [ ] syn:Payer syn:hasCovered syn:Encounter
            - [x] syn:Payer syn:hasCovered syn:Medication
            - [x] syn:Payer syn:hasPayerTransitionHistory syn:PayerTransition
        """
        rows = self.__resource_df.shape[0]
        # user_trust = generate_user_trust(rows)
        with alive_bar(rows, force_tty=True, title="Payer Conversion") as bar:
            for index, row in self.__resource_df.iterrows():
                # Create name of the payer class individual
                payer = payerUri(row["Id"])

                # Data Properties
                graph.add((payer, RDF.type, SYN.Payer))  # type
                graph.add((payer, SYN.id, urnUuidLiteral(row["Id"])))  # id
                graph.add((payer, SYN.name, plainLiteral(row["NAME"])))
                graph.add(
                    (payer, SYN.amountCovered, floatLiteral(row["AMOUNT_COVERED"]))
                )
                graph.add(
                    (payer, SYN.amountUncovered, floatLiteral(row["AMOUNT_UNCOVERED"]))
                )
                graph.add((payer, SYN.revenue, floatLiteral(row["REVENUE"])))
                graph.add(
                    (
                        payer,
                        SYN.coveredEncounters,
                        integerLiteral(row["COVERED_ENCOUNTERS"]),
                    )
                )
                graph.add(
                    (
                        payer,
                        SYN.uncoveredEncounters,
                        integerLiteral(row["UNCOVERED_ENCOUNTERS"]),
                    )
                )
                graph.add(
                    (
                        payer,
                        SYN.coveredMedications,
                        integerLiteral(row["COVERED_MEDICATIONS"]),
                    )
                )
                graph.add(
                    (
                        payer,
                        SYN.uncoveredMedications,
                        integerLiteral(row["UNCOVERED_MEDICATIONS"]),
                    )
                )
                graph.add(
                    (
                        payer,
                        SYN.coveredProcedures,
                        integerLiteral(row["COVERED_PROCEDURES"]),
                    )
                )
                graph.add(
                    (
                        payer,
                        SYN.uncoveredProcedures,
                        integerLiteral(row["UNCOVERED_PROCEDURES"]),
                    )
                )
                graph.add(
                    (
                        payer,
                        SYN.coveredImmunizations,
                        integerLiteral(row["COVERED_IMMUNIZATIONS"]),
                    )
                )
                graph.add(
                    (
                        payer,
                        SYN.uncoveredImmunizations,
                        integerLiteral(row["UNCOVERED_IMMUNIZATIONS"]),
                    )
                )
                graph.add(
                    (
                        payer,
                        SYN.uniqueCustomers,
                        integerLiteral(row["UNIQUE_CUSTOMERS"]),
                    )
                )
                graph.add((payer, SYN.qolsAvg, floatLiteral(row["QOLS_AVG"])))
                graph.add(
                    (payer, SYN.memberMonths, integerLiteral(row["MEMBER_MONTHS"]))
                )

                bar()


class PayerTransition(Resource):
    def __init__(self, df):
        self.__resource_df = df

    @property
    def resource_df(self):
        return self.__resource_df

    @resource_df.setter
    def resource_df(self, value):
        self.__resource_df = value

    def convert(self, graph):
        rows = self.__resource_df.shape[0]
        with alive_bar(
            rows, force_tty=True, title="Payer Transition Conversion"
        ) as bar:
            for index, row in self.__resource_df.iterrows():
                # Create name of the payertransition class individual
                payertransition = payertransitionUri(index)
                patient = patientUri(row["PATIENT"])
                payer = payerUri(row["PAYER"])

                # Data Properties
                graph.add((payertransition, RDF.type, SYN.PayerTransition))  # type
                graph.add(
                    (payertransition, SYN.patientId, urnUuidLiteral(row["PATIENT"]))
                )
                graph.add(
                    (
                        payertransition,
                        SYN.startYear,
                        dateLiteral(row["START_DATE"][:10]),
                    )
                )
                graph.add(
                    (payertransition, SYN.endYear, dateLiteral(row["END_DATE"][:10]))
                )
                graph.add((payertransition, SYN.payerId, urnUuidLiteral(row["PAYER"])))

                # Object Properties
                graph.add((payertransition, SYN.hasPatientRecord, patient))
                graph.add((patient, SYN.hasPayerTransitionHistory, payertransition))
                graph.add((payertransition, SYN.hasPayerRecord, payer))
                graph.add((payer, SYN.hasPayerTransitionHistory, payertransition))

                bar()


class Procedure(Resource):
    def __init__(self, df):
        self.__resource_df = df

    @property
    def resource_df(self):
        return self.__resource_df

    @resource_df.setter
    def resource_df(self, value):
        self.__resource_df = value

    def convert(self, graph):
        rows = self.__resource_df.shape[0]
        with alive_bar(rows, force_tty=True, title="Procedure Conversion") as bar:
            for index, row in self.__resource_df.iterrows():
                # Create name of the procedure class individual
                procedure = procedureUri(index)
                patient = patientUri(row["PATIENT"])
                encounter = encounterUri(row["ENCOUNTER"])

                # Data Properties
                graph.add((procedure, RDF.type, SYN.Procedure))   
                graph.add((procedure, SYN.startDateTime, dateTimeLiteral(row["START"])))
                if pd.notna(row["STOP"]):
                    graph.add((procedure, SYN.endDateTime, dateTimeLiteral(row["STOP"])))
                graph.add((procedure, SYN.patientId, urnUuidLiteral(row["PATIENT"])))
                if pd.notna(row["REASONCODE"]):
                    graph.add((procedure, SYN.reasoncode, snomedCtLiteral(row["REASONCODE"])))
                if pd.notna(row["REASONDESCRIPTION"]):
                    graph.add((procedure, SYN.reasondescription, plainLiteral(row["REASONDESCRIPTION"])))
                graph.add(
                    (procedure, SYN.encounterId, urnUuidLiteral(row["ENCOUNTER"]))
                )
                graph.add((procedure, SYN.code, snomedCtLiteral(row["CODE"])))
                graph.add(
                    (procedure, SYN.description, plainLiteral(row["DESCRIPTION"]))
                )
                graph.add((procedure, SYN.baseCost, floatLiteral(row["BASE_COST"])))

                # Object Properties
                graph.add((procedure, SYN.isOrderedFor, patient))
                graph.add((patient, SYN.hasHistoryOf, procedure))
                graph.add((procedure, SYN.isOrderedDuring, encounter))
                graph.add((encounter, SYN.hasOrdered, procedure))

                bar()


class Provider(Resource):
    def __init__(self, df):
        self.__resource_df = df

    @property
    def resource_df(self):
        return self.__resource_df

    @resource_df.setter
    def resource_df(self, value):
        self.__resource_df = value

    def convert(self, graph):
        rows = self.__resource_df.shape[0]
        # user_trust = generate_user_trust(rows)
        with alive_bar(rows, force_tty=True, title="Provider Conversion") as bar:
            for index, row in self.__resource_df.iterrows():
                # Create name of the provider class individual
                provider = providerUri(row["Id"])
                organization = organizationUri(
                    row["ORGANIZATION"]
                )  # for object property

                # Data Properties
                graph.add((provider, RDF.type, SYN.Provider))
                graph.add((provider, SYN.id, urnUuidLiteral(row["Id"])))
                graph.add(
                    (provider, SYN.organizationId, urnUuidLiteral(row["ORGANIZATION"]))
                )
                graph.add((provider, SYN.name, plainLiteral(row["NAME"])))
                graph.add((provider, SYN.gender, plainLiteral(row["GENDER"])))
                graph.add((provider, SYN.speciality, plainLiteral(row["SPECIALITY"])))
                graph.add((provider, SYN.address, plainLiteral(row["ADDRESS"])))
                graph.add((provider, SYN.city, plainLiteral(row["CITY"])))
                if "UTILIZATION" in self.__resource_df.columns:
                    graph.add(
                        (provider, SYN.utilization, integerLiteral(row["UTILIZATION"]))
                    )

                # Object Properties
                graph.add(
                    (
                        provider,
                        SYN.isAffiliatedWith,
                        organizationUri(row["ORGANIZATION"]),
                    )
                )
                graph.add((organization, SYN.hasEmployed, provider))

                bar()


class Supply(Resource):
    def __init__(self, df):
        self.__resource_df = df

    @property
    def resource_df(self):
        return self.__resource_df

    @resource_df.setter
    def resource_df(self, value):
        self.__resource_df = value

    def convert(self, graph):
        rows = self.__resource_df.shape[0]
        with alive_bar(rows, force_tty=True, title="Supply Conversion") as bar:
            for index, row in self.__resource_df.iterrows():
                # Create name of the supply class individual
                supply = supplyUri(index)
                patient = patientUri(row["PATIENT"])
                encounter = encounterUri(row["ENCOUNTER"])

                # Data Properties
                graph.add((supply, RDF.type, SYN.Supply))  # type
                graph.add((supply, SYN.date, dateLiteral(row["DATE"][:10])))
                graph.add((supply, SYN.patientId, urnUuidLiteral(row["PATIENT"])))
                graph.add((supply, SYN.encounterId, urnUuidLiteral(row["ENCOUNTER"])))
                graph.add((supply, SYN.code, snomedCtLiteral(row["CODE"])))
                graph.add((supply, SYN.description, plainLiteral(row["DESCRIPTION"])))
                graph.add((supply, SYN.quantity, integerLiteral(row["QUANTITY"])))

                # Object Properties
                graph.add((supply, SYN.isOrderedFor, patient))
                graph.add((patient, SYN.hasHistoryOf, supply))
                graph.add((supply, SYN.isOrderedDuring, encounter))
                graph.add((encounter, SYN.hasOrdered, supply))

                bar()
