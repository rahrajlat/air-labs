FROM apache/airflow:3.1.1
LABEL tag="airflow_docker:latest"
COPY requirements.txt .
#COPY airflow_xtra-0.1.0-py3-none-any.whl .
USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         vim \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
USER airflow
RUN pip install --no-cache-dir -r requirements.txt
#RUN pip install airflow_xtra-0.1.0-py3-none-any.whl