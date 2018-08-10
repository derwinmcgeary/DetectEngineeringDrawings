# Automatic file naming for Engineering Drawings

## Problem Definition

Engineering drawings come in various sizes, and they have an ID number in the bottom right which
defines which engineering drawing it is. Historically, this was all done by hand, and now there
are a large number of drawings which should be scanned into files which should then be named
according to the ID number.

The ID number has a format like `X-XXXX` or `X-XXXX/X` where X matches the regex `[0-9]`.


## Solution Sketch

We can use `aws s3 sync` to upload the scanned files to a known table, triggering a lambda function.
If we can run Rekognition for text on the scans, we should be able to find all text that matches
the regex and select the bottommost, rightmost one to use as the name. We can then: rename the
object in S3, record the results from Rekognition in a dynamoDB table with the original name as a
key, and generate a thumbnail with the recognised object on it for human verification. The final
step is to have a Powershell script and an API so that we can automatically rename all the original
files.

## Status

Pre-preliminary

Already tested: Rekognition can deal with numbers in neat handwriting.
Not tested: how Rekognition responds to real engineering drawings.


## Alternative ideas:

1. Preprocess by blurring all but the bottom-right corner of the image.
2. Use Mechanical Turk.