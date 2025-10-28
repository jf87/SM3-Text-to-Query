from synthea_rdf.graph import GraphBuilder
from pathlib import PurePath, Path
import time
import os
import yaml


def main():
    # Adjustement of configuration path based on the mount
    #with open("configuration.yaml", "r") as file:
    #    config = yaml.safe_load(file)
    # Configuration of csv file path adjusted to location on docker container
    with open("./synthea-rdf-converter-fork/configuration.yaml", "r") as file:
        config = yaml.safe_load(file)

    model_path = Path(config["model_path"]).resolve()
    synthea_csv_path = Path(config["synthea_csv_path"]).resolve()
    output_path = Path(config["output_path"]).resolve()
    chunk_size = config["chunk_size"]
    include_dua = config["include_dua"]
    include_trustscore = config["include_trustscore"]
    do_shutdown = config["do_shutdown"]
    skip = config["skip"]

    st = time.time()
    builder = GraphBuilder(
        csv_dir=synthea_csv_path,
        model_path=model_path,
        destination_dir=output_path,
        include_dua=include_dua,
        include_trustscore=include_trustscore,
        skip=skip,
    )

    convert(synthea_csv_path, output_path, builder, chunk_size=chunk_size)
    et = time.time()
    elapsed_time = et - st
    print(f"Elapsed time: {elapsed_time} seconds")

    if do_shutdown:
        os.system("shutdown now -h")


def convert(csv_path, dest_path, builder, chunk_size=500000):
    print(f"CSV file directory: {csv_path}")
    print(f"Destination directory: {dest_path}")
    print(f"Converting {PurePath(csv_path).name} ...")

    file_name = PurePath(csv_path).name
    graph = builder.build(chunk_size=chunk_size)
    # with alive_bar(
    #     title="Graph Serialization",
    #     unknown="waves2",
    # ) as bar:
    #     graph.serialize(destination=f"{dest_path}/{file_name}.ttl")
    #     bar()


if __name__ == "__main__":
    main()
