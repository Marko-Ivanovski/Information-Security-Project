<!-- WORKFLOW.md -->

# User‐Facing Workflow (Step by Step)

## User Registration (ZKP Setup)
1. On the “Register” page, the user chooses a username and creates a secret (e.g. a large random number or passphrase).  
2. The client (browser) computes a ZKP “public value” (for example, in a Schnorr scheme it would compute `V = g^x mod p` where `x` is the secret).  
3. Client sends `username + public value V` to `/register`.  
4. Server stores `(username, public value)` in PostgreSQL. No actual secret ever leaves the client.  
5. Server returns “Registration successful” (or an error if the username already exists).  

## User Login (ZKP Challenge‐Response)
1. On the “Login” page, user enters their username and secret (passphrase).  
2. Client looks up the stored public value `V` by first sending “I want to log in as USERNAME; give me the challenge” to `/login/initiate`.  
3. Server retrieves `V` from the database and responds with a random challenge `c`.  
4. Client computes the ZKP response `s` (e.g. `s = r + c · x mod q` or the equivalent in your chosen protocol), where `r` is a freshly chosen random nonce.  
5. Client sends back `(username, response s)` to `/login/verify`.  
6. Server verifies that `g^s ≡ R · V^c mod p` (or the appropriate check), where `R` was the original nonce commitment it temporarily stored.  
7. If the proof checks out, server creates a session (e.g. issues a secure session cookie or JWT) and redirects the user to their “Dashboard.” If it fails, show “Invalid credentials.”  

## Dashboard: Listing & Managing Files
1. After login, the user lands on `/dashboard`, which queries:  
    ```
    SELECT * FROM file_metadata WHERE owner = current_user_id;
    ```  
2. The template (`dashboard.html`) iterates over each file record, showing:  
   - Filename / upload date / file size  
   - Action buttons: `[Download]` `[Delete]` (and in the future, maybe `[Share]`).  
3. There is also an “Upload New File” button that links to `/upload`.  

## Uploading a File
1. User clicks “Upload New File,” which loads `/upload` (renders `upload.html`).  
2. In `upload.html`, the user selects a local file and (optionally) enters a short description or target recipient.  
3. Upon form submission, the browser does a POST to `/upload` (`multipart/form-data`).  
4. On the server, the Flask route for `/upload`:  
   - Checks `current_user` from session.  
   - Reads the file bytes; (optionally) encrypts them (e.g. using `cryptography.Fernet`) before writing.  
   - Saves the encrypted file to disk under `./storage/<user_id>/<random_filename>` inside the Docker volume.  
   - Inserts a row into `file_metadata` with columns like `(id, owner_id, original_filename, stored_path, upload_timestamp, sha256_hash, description)`.  
   - Redirects back to `/dashboard` with a “Upload successful” message.  

## Downloading a File
1. User clicks `[Download]` on a file in their dashboard. That hits `/download/<file_id>`.  
2. Server route:  
   - Verifies that `current_user_id == owner_id` for that `file_id` (or that the user has permission to access it).  
   - Reads the encrypted file from disk; (optionally) decrypts on‐the‐fly.  
   - Sends it back via `send_file(...)` with the original filename in the `Content‐Disposition` header.  
3. Browser prompts the user to save “mydocument.pdf” (or whatever it was called).  

## Deleting a File
1. User clicks `[Delete]` on their dashboard; this sends a POST (or DELETE) to `/delete/<file_id>`.  
2. Server route:  
   - Confirms `current_user_id` is owner.  
   - Deletes the file from disk (`os.remove(<stored_path>)`).  
   - Removes the row from `file_metadata`.  
   - Returns JSON `{ success: true }` or redirects back to dashboard with a flash message.  

## Logout
1. On every page’s header (in `base.html`), there is a `[Logout]` link that points to `/logout`.  
2. Hitting `/logout` clears the session cookie (or invalidates the JWT) and redirects back to `/login`.  
