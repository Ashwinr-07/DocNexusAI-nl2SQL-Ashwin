#!/bin/bash

PGHOST="127.0.0.1"
PGPORT="5433"
PGUSER="postgres"
DB_NAME="health_data_db"
DATA_DIR="./data"

echo "--- Ensure csvkit is installed ---"
command -v csvformat >/dev/null 2>&1 || { 
  echo "csvformat not found—installing csvkit..." 
  pip install csvkit 
}

echo "--- Converting CSVs to TSVs in $DATA_DIR ---"
for f in \
  payments_to_hcps \
  provider_details \
  referral_patterns \
  diagnosis_and_procedures \
  pharmacy_claims \
  conditions_directory \
  kol_providers \
  kol_scores
do
  echo "  • $f.csv → $f.tsv"
  csvformat -T "$DATA_DIR/${f}.csv" > "$DATA_DIR/${f}.tsv"
done

echo "--- Dropping and Creating Database: $DB_NAME ---"
dropdb --if-exists "$DB_NAME" -U "$PGUSER" -h "$PGHOST" -p "$PGPORT"
createdb    "$DB_NAME" -U "$PGUSER" -h "$PGHOST" -p "$PGPORT"

PSQL="psql -v ON_ERROR_STOP=1 -U $PGUSER -h $PGHOST -p $PGPORT -d $DB_NAME"

echo "--- Creating Tables ---"
$PSQL <<'EOF'
CREATE TABLE as_lsf_v1 (
    type_1_npi BIGINT,
    life_science_firm_name TEXT,
    product_name TEXT,
    nature_of_payment TEXT,
    year INTEGER,
    amount REAL
);

CREATE TABLE as_providers_v1 (
    type_1_npi BIGINT PRIMARY KEY,
    type_2_npi_names TEXT,
    type_2_npis TEXT,
    first_name TEXT,
    middle_name TEXT,
    last_name TEXT,
    gender VARCHAR(1),
    specialties TEXT,
    conditions_tags TEXT,
    conditions TEXT,
    cities TEXT,
    states TEXT,
    counties TEXT,
    city_states TEXT,
    hospital_names TEXT,
    system_names TEXT,
    affiliations TEXT,
    best_type_2_npi BIGINT,
    best_hospital_name TEXT,
    best_system_name TEXT,
    phone TEXT,
    email TEXT,
    linkedin TEXT,
    twitter TEXT
);

CREATE TABLE as_providers_referrals_v2 (
    primary_type_2_npi BIGINT,
    referring_type_2_npi BIGINT,
    primary_type_2_npi_city TEXT,
    referring_type_2_npi_city TEXT,
    primary_type_2_npi_state TEXT,
    referring_type_2_npi_state TEXT,
    primary_type_2_npi_postal_code TEXT,
    referring_type_2_npi_postal_code TEXT,
    primary_type_2_npi_lat DOUBLE PRECISION,
    referring_type_2_npi_lat DOUBLE PRECISION,
    primary_type_2_npi_lng DOUBLE PRECISION,
    referring_type_2_npi_lng DOUBLE PRECISION,
    primary_type_2_npi_name TEXT,
    referring_type_2_npi_name TEXT,
    primary_hospital_name TEXT,
    referring_hospital_name TEXT,
    primary_type_1_npi BIGINT,
    referring_type_1_npi BIGINT,
    primary_type_1_npi_name TEXT,
    referring_type_1_npi_name TEXT,
    primary_specialty TEXT,
    referring_specialty TEXT,
    date DATE,
    diagnosis_code TEXT,
    diagnosis_code_description TEXT,
    procedure_code TEXT,
    procedure_code_description TEXT,
    total_claim_charge DOUBLE PRECISION,
    total_claim_line_charge DOUBLE PRECISION,
    patient_count BIGINT
);

CREATE TABLE diagnosis_and_procedures (
    PATIENT_ID TEXT,
    CLAIM_NBR TEXT,
    CLAIM_TYPE_CD TEXT,
    CLAIM_CATEGORY TEXT,
    STATEMENT_FROM_DD DATE,
    PRIMARY_HCO TEXT,
    PRIMARY_HCO_NAME TEXT,
    PRIMARY_HCO_PROVIDER_CLASSIFICATION TEXT,
    PRIMARY_HCP TEXT,
    PRIMARY_HCP_SOURCE TEXT,
    PRIMARY_HCP_NAME TEXT,
    PRIMARY_HCP_SEGMENT TEXT,
    REFERRING_NPI_NBR TEXT,
    REFERRING_NPI_NM TEXT,
    PAYER_1_ID TEXT,
    PAYER_1_NAME TEXT,
    PAYER_1_SUBCHANNEL_NAME TEXT,
    PAYER_1_CHANNEL_NAME TEXT,
    CLAIM_CHARGE_AMT DOUBLE PRECISION,
    PRINCIPAL_DIAGNOSIS_CD TEXT,
    PRINCIPAL_DIAGNOSIS_VOCABULARY_ID TEXT,
    PRINCIPAL_DIAGNOSIS_DESC TEXT,
    HEADER_ANCHOR_DD DATE,
    SERVICE_FROM_DD DATE,
    RENDERING_PROVIDER_NPI_NBR TEXT,
    RENDERING_PROVIDER_NM TEXT,
    RENDERING_PROVIDER_CLASSTYPE TEXT,
    RENDERING_PROVIDER_SEGMENT TEXT,
    RENDERING_PROVIDER_ZIP TEXT,
    RENDERING_PROVIDER_STATE TEXT,
    REVENUE_CD TEXT,
    PROCEDURE_CD TEXT,
    PROCEDURE_VOCABULARY_ID TEXT,
    PROCEDURE_CODE_DESC TEXT,
    PROCEDURE_MODIFIER_1_CD TEXT,
    PROCEDURE_MODIFIER_1_DESC TEXT,
    NDC TEXT,
    CLAIM_LINE_CHARGE_AMT DOUBLE PRECISION,
    DAYS_OR_UNITS_VAL DOUBLE PRECISION,
    Version TEXT
);

CREATE TABLE fct_pharmacy_clear_claim_allstatus_cluster_brand (
    RX_ANCHOR_DD DATE,
    RX_CLAIM_NBR TEXT,
    PATIENT_ID TEXT,
    SERVICE_DATE_DD DATE,
    TRANSACTION_STATUS_NM TEXT,
    REJECT_REASON_1_CD TEXT,
    REJECT_REASON_1_DESC TEXT,
    NDC TEXT,
    NDC_DESC TEXT,
    NDC_GENERIC_NM TEXT,
    NDC_PREFERRED_BRAND_NM TEXT,
    NDC_DOSAGE_FORM_NM TEXT,
    NDC_DRUG_FORM_NM TEXT,
    NDC_DRUG_NM TEXT,
    NDC_DRUG_SUBCLASS_NM TEXT,
    NDC_DRUG_CLASS_NM TEXT,
    NDC_DRUG_GROUP_NM TEXT,
    NDC_ISBRANDED_IND TEXT,
    PRESCRIBED_NDC TEXT,
    DIAGNOSIS_CD TEXT,
    DAW_CD BIGINT,
    UNIT_OF_MEASUREMENT_CD TEXT,
    PRESCRIBER_NBR_QUAL_CD TEXT,
    PRESCRIBER_NPI_NBR TEXT,
    PRESCRIBER_NPI_NM TEXT,
    PRESCRIBER_NPI_ENTITY_CD BIGINT,
    PRESCRIBER_NPI_HCO_CLASS_OF_TRADE_DESC TEXT,
    PRESCRIBER_NPI_HCP_SEGMENT_DESC TEXT,
    PRESCRIBER_NPI_STATE_CD TEXT,
    PRESCRIBER_NPI_ZIP5_CD TEXT,
    PAYER_ID BIGINT,
    PAYER_PAYER_NM TEXT,
    PAYER_COB_SEQ_VAL BIGINT,
    PAYER_PLAN_SUBCHANNEL_CD TEXT,
    PAYER_PLAN_SUBCHANNEL_NM TEXT,
    PAYER_PLAN_CHANNEL_CD TEXT,
    PAYER_PLAN_CHANNEL_NM TEXT,
    PAYER_COMPANY_NM TEXT,
    PAYER_MCO_ISSUER_ID TEXT,
    PAYER_MCO_ISSUER_NM TEXT,
    PAYER_BIN_NBR TEXT,
    PAYER_PCN_NBR TEXT,
    PAYER_GROUP_STR TEXT,
    FILL_NUMBER_VAL BIGINT,
    DISPENSED_QUANTITY_VAL DECIMAL(38,9),
    PRESCRIBED_QUANTITY_VAL DECIMAL(38,9),
    DAYS_SUPPLY_VAL DECIMAL(38,9),
    NUMBER_OF_REFILLS_AUTHORIZED_VAL BIGINT,
    GROSS_DUE_AMT DECIMAL(38,9),
    TOTAL_PAID_AMT DECIMAL(38,9),
    PATIENT_TO_PAY_AMT DECIMAL(38,9),
    AWP_UNIT_PRICE_AMT DOUBLE PRECISION,
    AWP_CALC_AMT DOUBLE PRECISION
);

CREATE TABLE mf_conditions (
    projectId INTEGER,
    display TEXT,
    codingType TEXT,
    tcSize INTEGER
);

CREATE TABLE mf_providers (
    npi BIGINT PRIMARY KEY,
    docId TEXT,
    personId INTEGER,
    name TEXT,
    displayName TEXT,
    initials TEXT,
    familyName TEXT,
    score REAL,
    phone TEXT,
    isUSPrescriber BOOLEAN,
    sex VARCHAR(1),
    image TEXT,
    primaryOrgName TEXT,
    primaryOrgWebsite TEXT,
    highlyRatedConditionsCount INTEGER,
    orgLogo TEXT,
    orgWebsite TEXT,
    healthSystem_website TEXT,
    healthSystem_name TEXT,
    codingCount INTEGER,
    biography TEXT,
    gradInstitution_year INTEGER,
    gradInstitution_gradYearNumber INTEGER,
    gradInstitution_name TEXT,
    trainingInstitution_year INTEGER,
    trainingInstitution_gradYearNumber INTEGER,
    trainingInstitution_name TEXT
);

CREATE TABLE mf_scores (
    id INTEGER PRIMARY KEY,
    score REAL,
    mf_providers_npi BIGINT,
    mf_conditions_projectId INTEGER
);
EOF

echo "--- Copying Data From TSV Files ---"
$PSQL -c "\copy as_lsf_v1                             FROM '$DATA_DIR/payments_to_hcps.tsv'                         WITH (FORMAT csv, DELIMITER E'\t', HEADER true, NULL '');"
$PSQL -c "\copy as_providers_v1                       FROM '$DATA_DIR/provider_details.tsv'                        WITH (FORMAT csv, DELIMITER E'\t', HEADER true, NULL '');"
$PSQL -c "\copy as_providers_referrals_v2             FROM '$DATA_DIR/referral_patterns.tsv'                       WITH (FORMAT csv, DELIMITER E'\t', HEADER true, NULL '');"
$PSQL -c "\copy diagnosis_and_procedures              FROM '$DATA_DIR/diagnosis_and_procedures.tsv'                WITH (FORMAT csv, DELIMITER E'\t', HEADER true, NULL '');"
$PSQL -c "\copy fct_pharmacy_clear_claim_allstatus_cluster_brand FROM '$DATA_DIR/pharmacy_claims.tsv'                WITH (FORMAT csv, DELIMITER E'\t', HEADER true, NULL '');"
$PSQL -c "\copy mf_conditions                          FROM '$DATA_DIR/conditions_directory.tsv'                    WITH (FORMAT csv, DELIMITER E'\t', HEADER true, NULL '');"
$PSQL -c "\copy mf_providers                           FROM '$DATA_DIR/kol_providers.tsv'                           WITH (FORMAT csv, DELIMITER E'\t', HEADER true, NULL '');"
$PSQL -c "\copy mf_scores                              FROM '$DATA_DIR/kol_scores.tsv'                              WITH (FORMAT csv, DELIMITER E'\t', HEADER true, NULL '');"

echo "--- Database Setup and Data Import Complete ---"
