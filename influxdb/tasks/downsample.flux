// Task options
option task = {name: "downsample_10m_precision", every: 1h, offset: 0m}

// Data source
from(bucket: "dsmr")
    |> range(start: -task.every)
    |> filter(fn: (r) => r._measurement == "electricity")
    |> filter(fn: (r) => r._field == "used_peak" or r._field == "used_offpeak")
    |> aggregateWindow(every: 10m, fn: first)
    |> to(bucket: "dsmr-downsampled")
