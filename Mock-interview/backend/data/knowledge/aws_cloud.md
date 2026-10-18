# AWS and Cloud Computing

## Cloud service models: IaaS, PaaS, SaaS
IaaS (Infrastructure as a Service) rents virtual machines, storage and networks, for example Amazon EC2. PaaS (Platform as a Service) provides a managed platform to run code without handling servers, for example AWS Elastic Beanstalk. SaaS (Software as a Service) delivers finished applications over the internet, for example Gmail.

## EC2
Amazon EC2 (Elastic Compute Cloud) provides resizable virtual servers called instances. You choose the instance type (CPU and memory), the operating system image (AMI) and storage, and pay for the time the instance runs.

## S3
Amazon S3 (Simple Storage Service) is object storage: files (objects) are stored in buckets and accessed by key over HTTP. It is designed for 99.999999999 percent (eleven nines) durability and offers storage classes such as Standard, Infrequent Access and Glacier for archival.

## EBS vs S3 vs EFS
EBS is block storage attached to a single EC2 instance like a virtual hard disk. S3 is object storage accessed over the network, ideal for files, backups and static websites. EFS is a managed shared file system that many instances can mount at once.

## IAM
AWS Identity and Access Management controls who can do what. Users, groups and roles are granted permissions through JSON policies. Follow the principle of least privilege (grant only the permissions needed), use roles instead of long-term access keys for services, and enable MFA for important accounts.

## RDS and DynamoDB
Amazon RDS is a managed relational database service supporting engines such as MySQL, PostgreSQL, MariaDB, Oracle and SQL Server; AWS handles backups, patching and failover (Multi-AZ). Amazon DynamoDB is a managed NoSQL key-value and document database that scales automatically with single-digit-millisecond latency.

## Lambda and serverless
AWS Lambda runs your code in response to events (an HTTP call, a file uploaded to S3, a schedule) without you managing servers, and you pay only for the execution time. It is a core serverless service.

## VPC, subnets and security groups
A VPC (Virtual Private Cloud) is your isolated virtual network in AWS, divided into subnets (public subnets have a route to an internet gateway, private ones do not). Security groups are stateful firewalls attached to instances; network ACLs are stateless firewalls at the subnet level.

## Regions and Availability Zones
A Region is a geographic area with several isolated data centre groups called Availability Zones (AZs). Deploying across multiple AZs improves availability because one AZ failing does not take the application down.

## Scaling: vertical vs horizontal
Vertical scaling (scale up) makes one machine bigger with more CPU or RAM. Horizontal scaling (scale out) adds more machines behind a load balancer. AWS Auto Scaling adds or removes EC2 instances automatically based on demand, and Elastic Load Balancing spreads traffic across them.

## CloudWatch and monitoring
Amazon CloudWatch collects metrics, logs and events from AWS resources and applications, lets you build dashboards, and triggers alarms (for example to notify you or to scale out when CPU is high). AWS CloudTrail records API calls for auditing.

## Other common AWS services
Route 53 is DNS and domain registration. CloudFront is a content delivery network (CDN) that caches content near users. SQS is a message queue and SNS is a publish/subscribe notification service. SageMaker is a managed platform for building, training and deploying machine-learning models.

## Shared responsibility model
AWS is responsible for security "of" the cloud (physical data centres, hardware, the core infrastructure). The customer is responsible for security "in" the cloud: their data, IAM configuration, operating-system patching on EC2, network rules and encryption choices.
