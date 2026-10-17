+++
date = '{{ .Date }}'
draft = true
# 主栏目仅选一个：承德、生活、技术；遗址内容在 content/legacy/ 单独维护。
categories = ["生活"]
tags = []
title = '{{ replace .File.ContentBaseName "-" " " | title }}'
+++
