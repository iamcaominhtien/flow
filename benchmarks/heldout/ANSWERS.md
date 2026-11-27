# Answers (hidden from the agent under test)

Five questions per brief, with answers from the source. A grader answers them from the picture alone.

## h1-rebase (source: git's documented behaviour of `git rebase`; no file)

1. What does the rebase do with each commit of the branch? It replays (re-applies) them one at a time on top of the new base.
2. What happens when a commit does not apply cleanly? Git stops at that commit and waits for the user.
3. What can the user do at that point? Resolve the files, `git add` them and `git rebase --continue`; or `--skip` the commit; or `--abort`.
4. What does `--abort` lead to? The branch is put back as it was before the rebase started.
5. When is the rebase finished? When the last commit has been applied; the branch then points to the new tip.

## h2-redirect (source: `input/request.py`, `HTTPRedirectHandler`)

1. Which status codes are followed for a GET or HEAD? 301, 302, 303, 307 and 308.
2. Is a POST redirected, and how? Only on 301, 302 or 303, and the new request is a GET (a HEAD stays a HEAD); any other method or code raises `HTTPError`.
3. What happens when the redirect points to a scheme other than http, https or ftp? `HTTPError` is raised ("Redirection to url ... is not allowed").
4. What stops a redirect loop? At most 4 visits to the same URL and at most 10 redirections in all; past that, `HTTPError` with the infinite-loop message.
5. What happens to the request's headers? They are copied to the new request except `Content-Length` and `Content-Type`. (Also accepted: with no `Location` or `URI` header the handler returns nothing and the redirect is not followed.)

## h3-threadpool (source: `input/thread.py`)

1. When does `submit()` raise instead of queueing the task? When the pool is broken (`BrokenThreadPool`), after `shutdown()`, or during interpreter shutdown (`RuntimeError`).
2. When does `submit()` start a new thread? Only when no worker is idle (the idle semaphore cannot be taken) and the pool has fewer threads than `max_workers`.
3. What is the default number of workers? `min(32, CPU count + 4)`.
4. What happens to a task whose future was cancelled before a worker picked it up? The worker does not run it (`set_running_or_notify_cancel()` is false).
5. How do workers stop? `shutdown()` puts `None` on the queue; a worker that gets `None` while the pool is shut down puts `None` back for the others and exits. With `cancel_futures=True` the queued tasks are cancelled first. (Also accepted: if an initializer fails, the pool is marked broken and queued futures get `BrokenThreadPool`.)

## h4-meeting (source: `input/transcript.md`)

1. Who handles a refund of 200 euros or less? The agent, directly in the admin tool.
2. When does risk review a refund request? When the customer had more than two refunds in the last 90 days (the tool sets a "repeat" flag).
3. What happens after a rejection? The agent tells the customer; after a risk rejection a note is also added to the account, after a finance rejection it is not.
4. Where does finance issue an approved refund, and why there? From the payment provider, because the admin tool caps refunds at 200.
5. What happens when the payment fails? Finance retries once the next day; if it fails again, store credit is offered and the agent tells the customer.

## h5-tickets (source: `input/ticket_events.csv`)

1. Where can a new ticket go? To triaged, duplicate or spam.
2. Which statuses are final (nothing leaves them)? closed, closed_no_reply, duplicate, wont_fix and spam.
3. How does a resolved ticket come back into work? The customer reopens it (reopened), then it goes back to in_progress.
4. What happens while a ticket waits for the customer? It goes back to in_progress when the customer replies, or the system closes it as closed_no_reply. Waiting can start from triaged or from in_progress.
5. Where does escalation fit? From in_progress to escalated and back to in_progress.

## h6-deploy (source: `input/`)

1. What starts a production deployment? Pushing a tag that starts with `v`; it also needs a reviewer's approval (the `production` environment).
2. What must happen before an image is built and pushed? Lint and tests pass, and the event is a push (not a pull request).
3. When does staging deploy? On every push to `main`, after the image job, followed by the smoke test.
4. What happens when the production smoke test fails? A rollback to the last good tag of production (`.last_good_production`). In staging a failed smoke test only fails the job.
5. What happens when the Kubernetes rollout does not finish within 300 s? `kubectl rollout undo`, the step fails, and the last good tag is not updated.
