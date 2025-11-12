

n_points=1000000


data/.metadata/access_points/data.parquet: src/data/access_point_generator.py
	python -m src.data.access_point_generator \
		--n_points=$(n_points) \
		--output_path=data/.metadata/access_points/data.parquet

ap-data: data/.metadata/access_points/data.parquet
	@echo "Access points data generated at data/.metadata/access_points/data.parquet"

hourly-batch: data/.metadata/access_points/data.parquet
	python -m src.data.data_generator \
		--n_aps=$(n_points)