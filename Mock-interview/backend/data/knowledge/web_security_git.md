# Web Development, Security and Git

## REST API principles
REST is an architectural style for web APIs. Resources are identified by URLs, manipulated with standard HTTP methods, and usually exchanged as JSON. Key constraints: client-server separation, statelessness (each request carries all the information needed), a uniform interface, cacheability and a layered system.

## PUT vs PATCH vs POST
POST creates a new resource (not idempotent). PUT replaces a whole resource with the supplied representation (idempotent). PATCH applies a partial update to a resource.

## Authentication vs authorization
Authentication verifies who you are (logging in with a password). Authorization decides what you are allowed to do once identified (permissions and roles).

## Sessions vs JWT
With server-side sessions the server stores session data and gives the browser a session ID in a cookie. A JWT (JSON Web Token) is a signed token of the form header.payload.signature that carries claims, so the server can verify it without storing session state. The payload of a JWT is only base64-encoded, not encrypted, so never put secrets in it; tokens should expire.

## Password storage
Never store passwords in plain text. Store a salted hash made with a slow, purpose-built algorithm such as bcrypt, scrypt or Argon2, and compare hashes at login.

## CORS
Cross-Origin Resource Sharing is a browser mechanism that blocks a web page from calling an API on a different origin (scheme, host or port) unless the server allows it with response headers such as Access-Control-Allow-Origin. The restriction is enforced by the browser, not the server.

## SQL injection
SQL injection happens when untrusted input is concatenated into a SQL statement so an attacker can change the query. Prevent it with parameterised queries (prepared statements) or an ORM, plus input validation and least-privilege database accounts.

## XSS and CSRF
Cross-site scripting (XSS) injects malicious script into a page that other users view; prevent it by escaping output and using a Content Security Policy. Cross-site request forgery (CSRF) tricks a logged-in user's browser into sending an unwanted request; prevent it with CSRF tokens and SameSite cookies.

## ORM
An object-relational mapper (such as SQLAlchemy, Hibernate or Django ORM) maps database tables to classes and rows to objects, so you query the database with code instead of hand-written SQL.

## Flask vs FastAPI vs Django
Flask is a minimal micro-framework where you choose your own components. FastAPI is a modern framework built on type hints and Pydantic that validates requests automatically, supports async code and generates interactive OpenAPI documentation. Django is a full-featured framework with an ORM, admin panel and authentication built in.

## MVC pattern
Model-View-Controller separates an application into the Model (data and business logic), the View (what the user sees) and the Controller (handles input and coordinates the other two), which keeps code organised and testable.

## Docker containers vs virtual machines
A virtual machine includes a full guest operating system on top of a hypervisor. A container packages an application with its dependencies but shares the host operating system kernel, so it starts faster and uses fewer resources. A Docker image is the template and a container is a running instance of it.

## git pull vs git fetch
git fetch downloads new commits from the remote without changing your working files. git pull is fetch followed by merging those changes into your current branch.

## git merge vs git rebase
Merge joins two branches with a merge commit and keeps the full history. Rebase replays your commits on top of another branch to produce a linear history but rewrites commit hashes, so do not rebase branches that others are using.

## git reset vs git revert
git reset moves the branch pointer back and can discard commits, rewriting history. git revert creates a new commit that undoes an earlier commit, so it is safe on shared branches.

## Fork, clone and branch
A fork is your own copy of someone else's repository on the hosting service. A clone is a local copy of a repository. A branch is a separate line of development inside one repository. A pull request proposes merging your branch's changes for review.

## Resolving a merge conflict
A merge conflict occurs when two branches change the same lines. Git marks the conflicting sections in the file; you edit the file to keep the correct content, remove the conflict markers, stage the file with git add and complete the merge with a commit.
