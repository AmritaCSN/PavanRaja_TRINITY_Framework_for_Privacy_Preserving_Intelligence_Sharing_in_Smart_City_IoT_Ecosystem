#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NVFLARE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TRINITY_ROOT="$(cd "${NVFLARE_DIR}/.." && pwd)"
FABRIC_NET="${TRINITY_ROOT}/fabric-network"
LOG_DIR="${NVFLARE_DIR}/logs"
BIN_DIR="${TRINITY_ROOT}/bin"

mkdir -p "${LOG_DIR}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log()     { echo -e "${CYAN}[TRINITY]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail()    { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

log "================================================================"
log "  TRINITY FRAMEWORK — Phase 1 (fixed)"
log "  Root: ${TRINITY_ROOT}"
log "================================================================"

# Step 1
log "Step 1/8 — Checking prerequisites..."
command -v docker >/dev/null 2>&1 || fail "Docker not found"
docker compose version >/dev/null 2>&1 || fail "Docker Compose not found"
success "Docker:  $(docker --version | cut -d' ' -f3)"
success "Python:  $(python3.10 --version 2>&1)"
success "Node:    $(node --version)"
success "Go:      $(go version 2>&1 | cut -d' ' -f3)"

# Step 2 — Fabric binaries
log "Step 2/8 — Installing Hyperledger Fabric 2.5.4 binaries..."
mkdir -p "${BIN_DIR}"
if [ ! -f "${BIN_DIR}/peer" ]; then
    cd "${TRINITY_ROOT}"
    curl -sSLO https://raw.githubusercontent.com/hyperledger/fabric/main/scripts/bootstrap.sh
    chmod +x bootstrap.sh
    ./bootstrap.sh 2.5.4 1.5.7 -d -s 2>&1 | tee "${LOG_DIR}/fabric_install.log"
    [ -d "${TRINITY_ROOT}/bin" ] && success "Binaries in ${BIN_DIR}" || fail "Fabric binaries missing"
    rm -f bootstrap.sh
else
    success "Fabric binaries already present"
fi

export PATH="${BIN_DIR}:${PATH}"
export FABRIC_CFG_PATH="${FABRIC_NET}/config"
"${BIN_DIR}/peer" version >/dev/null 2>&1 && success "peer binary OK" || fail "peer binary broken"

# Step 3 — Crypto
log "Step 3/8 — Generating TLS certificates..."
if [ -d "${FABRIC_NET}/crypto-config/ordererOrganizations" ]; then
    warn "Crypto material exists — skipping"
else
    "${BIN_DIR}/cryptogen" generate \
        --config="${FABRIC_NET}/config/crypto-config.yml" \
        --output="${FABRIC_NET}/crypto-config" 2>&1 | tee "${LOG_DIR}/cryptogen.log"
    success "Crypto material generated"
fi

# Step 4 — Genesis + channel artifacts
log "Step 4/8 — Generating genesis block..."
[ ! -f "${FABRIC_NET}/config/genesis.block" ] && \
    "${BIN_DIR}/configtxgen" -profile TrinityGenesis -channelID system-channel \
        -outputBlock "${FABRIC_NET}/config/genesis.block" 2>&1 | tee "${LOG_DIR}/configtxgen.log" && \
    success "Genesis block created" || success "Genesis block exists"

[ ! -f "${FABRIC_NET}/config/city-intel-channel.tx" ] && \
    "${BIN_DIR}/configtxgen" -profile CityIntelChannel \
        -outputCreateChannelTx "${FABRIC_NET}/config/city-intel-channel.tx" \
        -channelID city-intel-channel 2>&1 >> "${LOG_DIR}/configtxgen.log" && \
    success "Channel tx created" || success "Channel tx exists"

for ORG in CityA CityB CityC; do
    [ ! -f "${FABRIC_NET}/config/${ORG}MSPanchors.tx" ] && \
        "${BIN_DIR}/configtxgen" -profile CityIntelChannel \
            -outputAnchorPeersUpdate "${FABRIC_NET}/config/${ORG}MSPanchors.tx" \
            -channelID city-intel-channel -asOrg "${ORG}MSP" 2>&1 >> "${LOG_DIR}/configtxgen.log"
done
success "All channel artifacts ready"

# Step 5 — Docker Compose
log "Step 5/8 — Starting Fabric network..."
cd "${NVFLARE_DIR}"
docker compose down --volumes --remove-orphans 2>/dev/null || true
log "Pulling images (may take 2-3 min on first run)..."
docker compose pull 2>&1 | tee "${LOG_DIR}/docker_pull.log"
docker compose up -d 2>&1 | tee "${LOG_DIR}/docker_compose.log"

log "Waiting 35s for peers to initialise..."
sleep 35

for C in orderer.trinity.local peer0.city_a.trinity.local peer0.city_b.trinity.local peer0.city_c.trinity.local trinity-api; do
    STATUS=$(docker inspect --format='{{.State.Status}}' "${C}" 2>/dev/null || echo "missing")
    [ "${STATUS}" = "running" ] && success "Container ${C}: running" || warn "Container ${C}: ${STATUS}"
done

# Step 6 — Channel
log "Step 6/8 — Creating city-intel-channel..."
sleep 10

CRYPTO_DOCKER="/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto"
ORDERER_CA_D="${CRYPTO_DOCKER}/ordererOrganizations/trinity.local/orderers/orderer.trinity.local/msp/tlscacerts/tlsca.trinity.local-cert.pem"
CH_ARTS="/opt/gopath/src/github.com/hyperledger/fabric/peer/channel-artifacts"

docker exec cli peer channel create \
    -o orderer.trinity.local:7050 -c city-intel-channel \
    -f ${CH_ARTS}/city-intel-channel.tx \
    --tls --cafile ${ORDERER_CA_D} \
    --outputBlock ${CH_ARTS}/city-intel-channel.block 2>&1 | tee "${LOG_DIR}/channel.log"

docker exec cli peer channel join -b ${CH_ARTS}/city-intel-channel.block 2>&1 | tee -a "${LOG_DIR}/channel.log"
success "City A joined"

for CITY in b c; do
    UPPER=$(echo $CITY | tr '[:lower:]' '[:upper:]')
    PORT=$( [ "$CITY" = "b" ] && echo 8051 || echo 9051 )
    docker exec \
        -e CORE_PEER_LOCALMSPID=City${UPPER}MSP \
        -e CORE_PEER_ADDRESS=peer0.city_${CITY}.trinity.local:${PORT} \
        -e CORE_PEER_TLS_CERT_FILE=${CRYPTO_DOCKER}/peerOrganizations/city_${CITY}.trinity.local/peers/peer0.city_${CITY}.trinity.local/tls/server.crt \
        -e CORE_PEER_TLS_KEY_FILE=${CRYPTO_DOCKER}/peerOrganizations/city_${CITY}.trinity.local/peers/peer0.city_${CITY}.trinity.local/tls/server.key \
        -e CORE_PEER_TLS_ROOTCERT_FILE=${CRYPTO_DOCKER}/peerOrganizations/city_${CITY}.trinity.local/peers/peer0.city_${CITY}.trinity.local/tls/ca.crt \
        -e CORE_PEER_MSPCONFIGPATH=${CRYPTO_DOCKER}/peerOrganizations/city_${CITY}.trinity.local/users/Admin@city_${CITY}.trinity.local/msp \
        cli peer channel join -b ${CH_ARTS}/city-intel-channel.block 2>&1 | tee -a "${LOG_DIR}/channel.log"
    success "City ${UPPER} joined"
done

# Step 7 — Chaincode
log "Step 7/8 — Deploying cti_audit chaincode..."
docker exec cli bash -c "cd /opt/gopath/src/github.com/chaincode/cti_audit && go mod tidy && go mod vendor" \
    2>&1 | tee "${LOG_DIR}/cc_build.log"

docker exec cli peer lifecycle chaincode package cti_audit.tar.gz \
    --path /opt/gopath/src/github.com/chaincode/cti_audit \
    --lang golang --label cti_audit_1.0 2>&1 | tee "${LOG_DIR}/cc_deploy.log"

docker exec cli peer lifecycle chaincode install cti_audit.tar.gz 2>&1 | tee -a "${LOG_DIR}/cc_deploy.log"
PKG_ID=$(docker exec cli peer lifecycle chaincode queryinstalled 2>&1 | grep 'Package ID' | awk '{print $3}' | tr -d ',')
log "Package ID: ${PKG_ID}"

docker exec cli peer lifecycle chaincode approveformyorg \
    -o orderer.trinity.local:7050 --channelID city-intel-channel \
    --name cti_audit --version 1.0 --sequence 1 --package-id "${PKG_ID}" \
    --tls --cafile ${ORDERER_CA_D} 2>&1 | tee -a "${LOG_DIR}/cc_deploy.log"
success "Approved: City A"

for CITY in b c; do
    UPPER=$(echo $CITY | tr '[:lower:]' '[:upper:]')
    PORT=$( [ "$CITY" = "b" ] && echo 8051 || echo 9051 )
    docker exec \
        -e CORE_PEER_LOCALMSPID=City${UPPER}MSP \
        -e CORE_PEER_ADDRESS=peer0.city_${CITY}.trinity.local:${PORT} \
        -e CORE_PEER_TLS_CERT_FILE=${CRYPTO_DOCKER}/peerOrganizations/city_${CITY}.trinity.local/peers/peer0.city_${CITY}.trinity.local/tls/server.crt \
        -e CORE_PEER_TLS_KEY_FILE=${CRYPTO_DOCKER}/peerOrganizations/city_${CITY}.trinity.local/peers/peer0.city_${CITY}.trinity.local/tls/server.key \
        -e CORE_PEER_TLS_ROOTCERT_FILE=${CRYPTO_DOCKER}/peerOrganizations/city_${CITY}.trinity.local/peers/peer0.city_${CITY}.trinity.local/tls/ca.crt \
        -e CORE_PEER_MSPCONFIGPATH=${CRYPTO_DOCKER}/peerOrganizations/city_${CITY}.trinity.local/users/Admin@city_${CITY}.trinity.local/msp \
        cli peer lifecycle chaincode install cti_audit.tar.gz 2>&1 | tee -a "${LOG_DIR}/cc_deploy.log"
    docker exec \
        -e CORE_PEER_LOCALMSPID=City${UPPER}MSP \
        -e CORE_PEER_ADDRESS=peer0.city_${CITY}.trinity.local:${PORT} \
        -e CORE_PEER_TLS_CERT_FILE=${CRYPTO_DOCKER}/peerOrganizations/city_${CITY}.trinity.local/peers/peer0.city_${CITY}.trinity.local/tls/server.crt \
        -e CORE_PEER_TLS_KEY_FILE=${CRYPTO_DOCKER}/peerOrganizations/city_${CITY}.trinity.local/peers/peer0.city_${CITY}.trinity.local/tls/server.key \
        -e CORE_PEER_TLS_ROOTCERT_FILE=${CRYPTO_DOCKER}/peerOrganizations/city_${CITY}.trinity.local/peers/peer0.city_${CITY}.trinity.local/tls/ca.crt \
        -e CORE_PEER_MSPCONFIGPATH=${CRYPTO_DOCKER}/peerOrganizations/city_${CITY}.trinity.local/users/Admin@city_${CITY}.trinity.local/msp \
        cli peer lifecycle chaincode approveformyorg \
        -o orderer.trinity.local:7050 --channelID city-intel-channel \
        --name cti_audit --version 1.0 --sequence 1 --package-id "${PKG_ID}" \
        --tls --cafile ${ORDERER_CA_D} 2>&1 | tee -a "${LOG_DIR}/cc_deploy.log"
    success "Approved: City ${UPPER}"
done

docker exec cli peer lifecycle chaincode commit \
    -o orderer.trinity.local:7050 --channelID city-intel-channel \
    --name cti_audit --version 1.0 --sequence 1 \
    --tls --cafile ${ORDERER_CA_D} \
    --peerAddresses peer0.city_a.trinity.local:7051 \
    --tlsRootCertFiles ${CRYPTO_DOCKER}/peerOrganizations/city_a.trinity.local/peers/peer0.city_a.trinity.local/tls/ca.crt \
    --peerAddresses peer0.city_b.trinity.local:8051 \
    --tlsRootCertFiles ${CRYPTO_DOCKER}/peerOrganizations/city_b.trinity.local/peers/peer0.city_b.trinity.local/tls/ca.crt \
    --peerAddresses peer0.city_c.trinity.local:9051 \
    --tlsRootCertFiles ${CRYPTO_DOCKER}/peerOrganizations/city_c.trinity.local/peers/peer0.city_c.trinity.local/tls/ca.crt \
    2>&1 | tee -a "${LOG_DIR}/cc_deploy.log"
success "cti_audit committed on city-intel-channel"

docker exec cli peer chaincode invoke \
    -o orderer.trinity.local:7050 --channelID city-intel-channel --name cti_audit \
    --tls --cafile ${ORDERER_CA_D} \
    -c '{"function":"InitLedger","Args":[]}' \
    --peerAddresses peer0.city_a.trinity.local:7051 \
    --tlsRootCertFiles ${CRYPTO_DOCKER}/peerOrganizations/city_a.trinity.local/peers/peer0.city_a.trinity.local/tls/ca.crt \
    2>&1 | tee -a "${LOG_DIR}/cc_deploy.log"
success "InitLedger complete"

# Step 8 — NVFLARE
log "Step 8/8 — Provisioning NVFLARE workspace..."
cd "${NVFLARE_DIR}"
python3.10 -m nvflare.lighter.provision -p project.yml 2>&1 | tee "${LOG_DIR}/nvflare_provision.log"
success "NVFLARE workspace provisioned"

echo ""
log "================================================================"
log "  Phase 1 COMPLETE"
log "  API: http://192.168.141.201:3000/health"
log "  Logs: ${LOG_DIR}/"
log "  Next: Phase 2 — Data Engineering"
log "================================================================"
