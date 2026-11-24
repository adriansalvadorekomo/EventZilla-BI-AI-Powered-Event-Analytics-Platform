# Airflow with dbt and Great Expectations, each in its own virtualenv (their dependency pins differ from Airflow's).
FROM apache/airflow:2.10.5-python3.11
USER root
RUN python -m venv /opt/dbt && /opt/dbt/bin/pip install --no-cache-dir dbt-core==1.10.13 dbt-postgres==1.9.1 \
 && python -m venv /opt/gx && /opt/gx/bin/pip install --no-cache-dir "great_expectations[postgresql]==1.25.0" \
 && chown -R airflow: /opt/dbt /opt/gx
USER airflow
RUN pip install --no-cache-dir pandas==2.3.3 openpyxl==3.1.5 boto3==1.40.70 requests==2.32.5 hijridate==2.6.0
