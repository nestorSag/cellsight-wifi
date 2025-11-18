

n_points=1000000
tag=latest

data/.metadata/access_points/data.parquet: src/data/access_point_generator.py
	conda run -n cellsight python -m src.data.access_point_generator \
		--n_points=$(n_points) \
		--output_path=data/.metadata/access_points/data.parquet

ap-data: data/.metadata/access_points/data.parquet
	@echo "Access points data generated at data/.metadata/access_points/data.parquet"

hourly-batch: data/.metadata/access_points/data.parquet
	conda run -n cellsight python -m src.data.data_generator \
		--n_aps=$(n_points)

preprocess: 
	conda run -n cellsight python -m src.preproc

make env:
	conda env create -n cellsight -f environment.yaml -p ./env

# image:
# 	source .env && docker build -t cellsight-wifi:$(tag) --build-arg PWD=$(tag) .

questdb:
	docker run \
	  --network host \
	  -p 9000:9000 \
	  -p 9009:9009 \
	  -p 8812:8812 \
	  -p 9003:9003 \
	  questdb/questdb:9.2.0
