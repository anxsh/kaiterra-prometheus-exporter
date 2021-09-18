# kaiterra-prometheus-exporter

Simple web server that exports Prometheus metrics for Kaiterra devices (LaserEgg+ Chemical).

# Build

```
docker build -t kaiterra-prometheus-exporter .
```

# Run

```
docker run -it -p PORT:PORT --rm --name kaiterra-prometheus-exporter kaiterra-prometheus-exporter:latest
```
