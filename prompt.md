This project is a proof of concept for the backend of an analytics dashboard that processes wifi modem telemetry at scale for multiple million devices using the Python ecosystem.

# Key principles

- Use a test driven development approach
- Always ensure you handle possible exceptions gracefully

The structure of this project is a Python package that perform different tasks:

## First module (or subpackage): dummy data generator
This package produces dummy data that helps stress-test the project in anticipation of the real data sets. The dummy data is wifi telemetry from several million wifi points in the U.S. The real data is comprised by hourly measurements of 20 million wifi devices across the U.S.. The ID columns are as follows:

* datetime string
* region (string, US region)
* state (string, US state)
* latitude (float, continental US)
* longitude (float, continental US)
* site (int, unique)
* cell (int between 1 and 10)
* sector (int between 1 and 10)
* band (int between 1 and 10)

In addition to this, there are 20 metrics for each device. These metrics can be random floats and have arbitrary names such as `metric_1`, etc. We can assume there are no missing values.

This is how I think it should work:

1. When run for the first time, the package creates a `parquet` file of K million rows with ID columns. This file is kept so that dummy hourly data has consistent IDs. A "current time" should also be kept track of. The initial date can be 01-01-2020, and each time an hourly batch of data is generated, the current time is bumped up. This will help keep consistent dates in the dashboard prototypes. Please make sure that the sampled lat/lon are actually in the continental U.S.; for now, it's fine to just take a random sample over the U.S. geometry.

2. When the package generates dummy data, it just produces and appends random metrics for the ID rows, and saves the resulting data as a CSV file in a user-provided folder. CSV is a necessary format as production data will come in this format.


## Second module (or subpackage): transforming data to parquet format
This package should take a folder with CSV files, transform them into parquet files, and store the results in a partitioned parquet directory. Let's start with the following partition:


date/
  hour/
    region/
      state/ 
        
the date shuld be extracted from the datetime string in the format `dd-mm-yy`, and hour should go from 0 to 23. 



## Tasks

### 1. Set up

Create 
