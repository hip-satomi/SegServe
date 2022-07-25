from datetime import datetime
from typing import List

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# bucket to write to
bucket = "service_stats"


def influxdb_report_images(object_counts: List[int], **tags):
    """Reports the counts for a batched prediction to influx

    Args:
        object_counts (List[int]): list of object numbers detected in the respective images
    """

    # initialize client from environment properties
    with InfluxDBClient.from_env_properties() as client:
        # setup write api
        write_api = client.write_api(write_options=SYNCHRONOUS)

        # get current time
        now = datetime.utcnow()

        # loop over frame counts
        for i,count in enumerate(object_counts):
            point = Point("segmentation")
            # add all tags
            for tag,value in tags.items():
                point = point.tag(tag, value)
            # specify the batch index as tag
            point.tag("batch_index", i)
            # add the count field
            point.field("count", count)
            # set the time
            point.time(now, WritePrecision.NS)

            # write (will already be batched)
            write_api.write(bucket=bucket, record=point)

        # close client
        client.close()

def influxdb_report_timing(duration: float, num_objects: int, num_images: int, **tags):
    """Reports prediction timings, total number of objects and images to influx

    Args:
        duration (float): Duration of the prediction.
        num_objects (int): Total number of predicted objects.
        num_images (int): Number of images for prediction.
    """

    # initialize client from environment properties
    with InfluxDBClient.from_env_properties() as client:
        # setup write api
        write_api = client.write_api(write_options=SYNCHRONOUS)

        # get current time
        now = datetime.utcnow()

        point = Point("segmentation_duration")
        # add all tags
        for tag,value in tags.items():
            point = point.tag(tag, value)

        # add the measured values
        point.field("duration", duration)
        point.field("num_objects", num_objects)
        point.field("num_images", num_images)

        write_api.write(bucket=bucket, record=point)

        client.close()
