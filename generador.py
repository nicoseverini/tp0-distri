import sys

output = sys.argv[1]
clients = int(sys.argv[2])

with open(output, "w") as f:
    f.write("name: tp0\n")
    f.write("services:\n")

    f.write("  server:\n")
    f.write("    container_name: server\n")
    f.write("    image: server:latest\n")
    f.write("    entrypoint: python3 /main.py\n")
    f.write("    environment:\n")
    f.write("      - PYTHONUNBUFFERED=1\n")
    f.write("    networks:\n")
    f.write("      - testing_net\n")
    f.write("    volumes:\n")
    f.write("      - ./server/config.ini:/config.ini\n")

    f.write("    healthcheck:\n")
    f.write("      test: [\"CMD\", \"python3\", \"-c\", \"import socket; s=socket.socket(); s.settimeout(1); s.connect(('localhost',12345))\"]\n")
    f.write("      interval: 1s\n")
    f.write("      timeout: 1s\n")
    f.write("      retries: 10\n\n")

    for i in range(1, clients + 1):
        f.write(f"  client{i}:\n")
        f.write(f"    container_name: client{i}\n")
        f.write("    image: client:latest\n")
        f.write("    entrypoint: /client\n")
        f.write("    environment:\n")
        f.write(f"      - CLI_ID={i}\n")
        f.write("    networks:\n")
        f.write("      - testing_net\n")
        f.write("    volumes:\n")
        f.write("      - ./client/config.yaml:/config.yaml\n")

        f.write("    depends_on:\n")
        f.write("      server:\n")
        f.write("        condition: service_healthy\n\n")

    f.write("networks:\n")
    f.write("  testing_net:\n")
    f.write("    ipam:\n")
    f.write("      driver: default\n")
    f.write("      config:\n")
    f.write("        - subnet: 172.25.125.0/24\n")