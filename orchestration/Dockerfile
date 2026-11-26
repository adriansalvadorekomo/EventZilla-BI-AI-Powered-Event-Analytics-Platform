# Airflow with dbt and Great Expectations, each in its own virtualenv (their dependency pins differ from Airflow's).
FROM apache/airflow:2.11.2-python3.11
USER root
RUN python -m venv /opt/dbt && /opt/dbt/bin/pip install --no-cache-dir dbt-core==1.10.13 dbt-postgres==1.9.1 \
 && python -m venv /opt/gx && /opt/gx/bin/pip install --no-cache-dir "great_expectations[postgresql]==1.25.0" \
 && mkdir -p /opt/eventzilla-runtime && chown -R airflow: /opt/dbt /opt/gx /opt/eventzilla-runtime
USER airflow
# landing and scraping tasks run in Airflow's own environment: install against Airflow's tested constraints
RUN pip install --no-cache-dir "apache-airflow==2.10.5" pandas openpyxl boto3 requests hijridate==2.6.0       --constraint https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.11.txt
