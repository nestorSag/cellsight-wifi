
CONDA := $(shell command -v mamba >/dev/null 2>&1 && echo mamba || echo $(CONDA))

n_points=10000000 # 10M
tag=latest

.PHONY: ap-data hourly-batch preprocess env questdb

data/.metadata/access_points/data.parquet: src/data/access_point_generator.py
	$(CONDA) run -p ./env python -m src.data.access_point_generator \
		--n_points=$(n_points) \
		--output_path=data/.metadata/access_points/data.parquet

ap-data: data/.metadata/access_points/data.parquet
	@echo "Access points data generated at data/.metadata/access_points/data.parquet"

hourly-batch: data/.metadata/access_points/data.parquet
	$(CONDA) run -p ./env python -m src.data.data_generator \
		--n_aps=$(n_points)

preprocess: 
	$(CONDA) run -p ./env python -m src.preproc
env/bin/python:
	$(CONDA) create -p ./env -f environment.yaml -y

env: env/bin/python

# image:
# 	source .env && docker build -t cellsight-wifi:$(tag) --build-arg PWD=$(tag) .

questdb:
	docker run \
	  --network host \
	  -p 9000:9000 \
	  -p 9009:9009 \
	  -p 8812:8812 \
	  -p 9003:9003 \
	  -e QDB_LINE_HTTP_ENABLED=true \
	  questdb/questdb:9.2.0
