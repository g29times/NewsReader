#!/bin/bash
cd /teamspace/studios/this_studio/NewsReader
git add articles.db
git commit -m "Auto commit on $(date +'%Y-%m-%d %H:%M:%S')"
git push origin master