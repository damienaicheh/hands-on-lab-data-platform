## Terraform Azure deployment

This repository contains Terraform code to deploy resources in Azure. Follow the steps below to set up and deploy your infrastructure.

```bash
cd infra
```

Login to Azure using the device code method:

```bash
az login --use-device-code
```

Terraform initialization:

```bash
terraform init
```

Terraform planning commands:

```bash
terraform plan -out plan.out
```

Terraform applying commands:

```bash
terraform apply plan.out
```