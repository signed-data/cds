#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { SignedDataStack } from "../lib/signeddata-stack.js";

const app = new cdk.App();

new SignedDataStack(app, "SignedDataStack", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region:  process.env.CDK_DEFAULT_REGION ?? "us-east-1",
  },
  tags: {
    Project:   "signeddata-cds",
    ManagedBy: "cdk",
  },
});
