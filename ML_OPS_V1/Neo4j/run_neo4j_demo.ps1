# Helper script to run the Neo4j demo with a local container.
# Usage: Open PowerShell in the repo root and run:
#   .\run_neo4j_demo.ps1

$composeFile = "docker-compose.neo4j.yml"
$neo4jUri = "bolt://localhost:7687"
$neo4jUser = "neo4j"
$neo4jPassword = "password"

Write-Output "Bringing up Neo4j container (docker-compose neo4j)..."
docker compose -f $composeFile up -d

# Wait for BOLT port to be available
Write-Output "Waiting for Neo4j BOLT port 7687 to be available..."
$maxAttempts = 30
$attempt = 0
while ($attempt -lt $maxAttempts) {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $async = $tcp.BeginConnect('127.0.0.1', 7687, $null, $null)
        $wait = $async.AsyncWaitHandle.WaitOne(1000)
        if ($wait -and $tcp.Connected) {
            $tcp.EndConnect($async)
            $tcp.Close()
            Write-Output "Neo4j appears ready."
            break
        }
    } catch {
        # ignore
    }
    Start-Sleep -Seconds 2
    $attempt++
    Write-Output "Waiting... ($attempt/$maxAttempts)"
}
if ($attempt -ge $maxAttempts) {
    Write-Error "Timed out waiting for Neo4j to start. Check docker logs."
    exit 1
}

# Ensure Python deps are installed into the active environment
Write-Output "Installing Python requirements from src/requirements.txt..."
python -m pip install -r src/requirements.txt

# Export env vars for the demo script
$env:NEO4J_URI = $neo4jUri
$env:NEO4J_USER = $neo4jUser
$env:NEO4J_PASSWORD = $neo4jPassword

Write-Output "Running neo4j_demo.py"
python src\neo4j_demo.py

# Optionally tear down the container (commented out by default)
# Write-Output "Tearing down Neo4j container..."
# docker compose -f $composeFile down

Write-Output "Done."
