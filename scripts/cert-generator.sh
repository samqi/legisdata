#!/usr/bin/env bash

logger -s Resetting certificate folder
rm -rf certificates
mkdir -p certificates/{root,admin,node,client,dev}
ls -l certificates
echo

logger -s Refer to https://opensearch.org/docs/latest/security/configuration/generate-certificates/ to generate certificate

logger -s Generate a private key
openssl genrsa -out certificates/root/root-ca-key.pem 2048
ls -l certificates/root/root-ca-key.pem
echo

logger -s Generate a root certificate
openssl req -new -x509 -sha256 -subj "/C=MY/ST=Selangor/L=Subang Jaya/O=Sinarproject/OU=Sinarproject/CN=sinarproject.org" -key certificates/root/root-ca-key.pem -out certificates/root/root-ca.pem -days 730
ls -l certificates/root/root-ca.pem
echo

logger -s Create a crt for root
openssl x509 -outform der -in certificates/root/root-ca.pem -out certificates/root/root-ca.crt
ls -l certificates/root/root-ca.crt
echo

logger -s Generating a private key for admin
openssl genrsa -out certificates/admin/admin-key-temp.pem 2048
ls -l certificates/admin/admin-key-temp.pem
echo

logger -s Converting the key for admin
openssl pkcs8 -inform PEM -outform PEM -in certificates/admin/admin-key-temp.pem -topk8 -nocrypt -v1 PBE-SHA1-3DES -out certificates/admin/admin-key.pem
chmod +r certificates/admin/admin-key.pem
ls -l certificates/admin/admin-key.pem
echo

logger -s Creating a certificate signing request for admin
openssl req -new -subj "/C=MY/ST=Selangor/L=Subang Jaya/O=Sinarproject/OU=Legisdata/CN=legislativedata.sinarproject.org" -key certificates/admin/admin-key.pem -out certificates/admin/admin.csr
ls -l certificates/admin/admin.csr
echo

logger -s Creating a certificate for admin
openssl x509 -req -in certificates/admin/admin.csr -CA certificates/root/root-ca.pem -CAkey certificates/root/root-ca-key.pem -CAcreateserial -sha256 -out certificates/admin/admin.pem -days 730
ls -l certificates/admin/admin.pem
echo

logger -s Creating a private key for node
openssl genrsa -out certificates/node/node-key-temp.pem 2048
ls -l certificates/node/node-key-temp.pem
echo

logger -s Converting the key for node
openssl pkcs8 -inform PEM -outform PEM -in certificates/node/node-key-temp.pem -topk8 -nocrypt -v1 PBE-SHA1-3DES -out certificates/node/node-key.pem
chmod +r certificates/node/node-key.pem
ls -l certificates/node/node-key.pem
echo

logger -s Creating a certificate signing request for node
#openssl req -new -subj "/C=MY/ST=Selangor/L=Subang Jaya/O=Sinarproject/OU=Legisdata/CN=legislativedata.sinarproject.org" -key certificates/node/node-key.pem -out certificates/node/node.csr
openssl req -new -subj "/C=MY/ST=Selangor/L=Subang Jaya/O=Sinarproject/OU=Legisdata/CN=search-node" -key certificates/node/node-key.pem -out certificates/node/node.csr
ls -l certificates/node/node.csr
echo

#logger -s Creating a SAN extension for node
#echo 'subjectAltName=DNS:legislativedata.sinarproject.org' > certificates/node/node.ext
#ls -l certificates/node/node.ext
#echo

logger -s Creating a certificate for node
#openssl x509 -req -in certificates/node/node.csr -CA certificates/root/root-ca.pem -CAkey certificates/root/root-ca-key.pem -CAcreateserial -sha256 -out certificates/node/node.pem -days 730 -extfile certificates/node/node.ext
openssl x509 -req -in certificates/node/node.csr -CA certificates/root/root-ca.pem -CAkey certificates/root/root-ca-key.pem -CAcreateserial -sha256 -out certificates/node/node.pem -days 730
ls -l certificates/node/node.pem
echo

logger -s Creating a private key for client
openssl genrsa -out certificates/client/client-key-temp.pem 2048
ls -l certificates/client/client-key-temp.pem
echo

logger -s Converting the key for client
openssl pkcs8 -inform PEM -outform PEM -in certificates/client/client-key-temp.pem -topk8 -nocrypt -v1 PBE-SHA1-3DES -out certificates/client/client-key.pem
ls -l certificates/client/client-key.pem
echo

logger -s Creating a certificate signing request for client
#openssl req -new -subj "/C=MY/ST=Selangor/L=Subang Jaya/O=Sinarproject/OU=Legisdata/CN=legislativedata.sinarproject.org" -key certificates/client/client-key.pem -out certificates/client/client.csr
openssl req -new -subj "/C=MY/ST=Selangor/L=Subang Jaya/O=Sinarproject/OU=Legisdata/CN=search-client" -key certificates/client/client-key.pem -out certificates/client/client.csr
ls -l certificates/client/client.csr
echo

#logger -s Creating a SAN extension for client
#echo 'subjectAltName=DNS:legislativedata.sinarproject.org' > certificates/client/client.ext
#ls -l certificates/client/client.ext
#echo

logger -s Creating a certificate for client
#openssl x509 -req -in certificates/client/client.csr -CA certificates/root/root-ca.pem -CAkey certificates/root/root-ca-key.pem -CAcreateserial -sha256 -out certificates/client/client.pem -days 730 -extfile certificates/client/client.ext
openssl x509 -req -in certificates/client/client.csr -CA certificates/root/root-ca.pem -CAkey certificates/root/root-ca-key.pem -CAcreateserial -sha256 -out certificates/client/client.pem -days 730
ls -l certificates/client/client.pem
echo

logger -s Creating a private key for dev
openssl genrsa -out certificates/dev/dev-key-temp.pem 2048
ls -l certificates/dev/dev-key-temp.pem
echo

logger -s Converting the key for dev
openssl pkcs8 -inform PEM -outform PEM -in certificates/dev/dev-key-temp.pem -topk8 -nocrypt -v1 PBE-SHA1-3DES -out certificates/dev/dev-key.pem
chmod +r certificates/dev/dev-key.pem
ls -l certificates/dev/dev-key.pem
echo

logger -s Creating a certificate signing request for dev
openssl req -new -subj "/C=MY/ST=Selangor/L=Subang Jaya/O=Sinarproject/OU=Legisdata/CN=localhost" -key certificates/dev/dev-key.pem -out certificates/dev/dev.csr
ls -l certificates/dev/dev.csr
echo

logger -s Creating a certificate for dev
openssl x509 -req -in certificates/dev/dev.csr -CA certificates/root/root-ca.pem -CAkey certificates/root/root-ca-key.pem -CAcreateserial -sha256 -out certificates/dev/dev.pem -days 730
ls -l certificates/dev/dev.pem
echo

logger -s Printing the disgtinguished names
echo "ADMIN: $(openssl x509 -subject -nameopt RFC2253 -noout -in certificates/admin/admin.pem | cut -c9-)"
echo "NODE: $(openssl x509 -subject -nameopt RFC2253 -noout -in certificates/node/node.pem | cut -c9-)"
echo "CLIENT: $(openssl x509 -subject -nameopt RFC2253 -noout -in certificates/client/client.pem | cut -c9-)"
echo "DEV: $(openssl x509 -subject -nameopt RFC2253 -noout -in certificates/dev/dev.pem | cut -c9-)"