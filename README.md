# ebooks2

new and improved!

## development

0. install system dependencies.

   ```
   brew install aws-cdk awscli python
   aws configure --profile spookyhouse
   ```

1. install application dependencies in a virtual environment.

   ```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip wheel
   pip install -r requirements.txt
   ```

2. write code, (eventually) testing with `pytest`.

3. deploy `StableEbooksStack` to set up some infrastructure. this creates an s3 bucket (`steve-ebooks`) as a prerequisite for the next step. it also looks up route53 hosted zone by its domain name (`spookyhouse.co.uk`) and creates a certificate for it, because it slow to roll back.

   ```
   cdk --profile spookyhouse deploy StableEbooksStack
   ```

4. build and deploy the code.

   ```
   ./build.sh
   python deploy.py  # TODO
   ```

5. deploy `EbooksStack` to set up the rest of the infrastructure. this creates lambdas from the code uploaded to the `steve-ebooks` bucket in the previous step and an "http api" (`ebooks-api` via api gateway) to trigger them.

   ```
   cdk --profile spookyhouse deploy EbooksStack
   ```

if everything worked, https://ebooks.spookyhouse.co.uk/ should be live.
