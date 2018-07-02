#!/usr/bin/env python
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import json
import os
import sys
import requests
import argparse
import subprocess
import urllib
import hashlib

l_path = os.path.realpath(os.path.dirname(__file__))
os.chdir(os.path.dirname(l_path))
sys.path.append(".")

#------------------------------------------------------------------#

class StatusHelper:
  def __init__(self):
    self.m_dryrun = False
    self.m_parser = argparse.ArgumentParser("coverxygen build checker")
    self.m_parser.add_argument("--token",    help="Github API secret token",                 dest="m_token",     required=True)
    self.m_parser.add_argument("--build-id", help="Travis build-id",                         dest="m_buildID",   required=True)
    self.m_parser.add_argument("--commit",   help="Current git commit hash",                 dest="m_commit",    required=True)
    self.m_parser.add_argument("--pull-id",  help="Current pull request, false if not a PR", dest="m_prid",      required=True)
    self.m_parser.add_argument("--dry-run",  help="Do not push statuses to github",          dest="m_dryrun",    action="store_true")
    self.m_parser.parse_args(sys.argv[1:], self)
    self.m_comment = ""
    l_md5 = hashlib.md5()
    l_md5.update(self.m_token.encode('utf-8'))
    print("build-id   : %s" % str(self.m_buildID))
    print("commit     : %s" % str(self.m_commit))
    print("pull-id    : %s" % str(self.m_prid))

  def get_pr_commit(self):
    if self.m_dryrun:
      return {}

    l_params  = { "access_token" : self.m_token }
    l_headers = { "Content-Type" : "application/json" }
    l_url     = "https://api.github.com/repos/%(user)s/%(repo)s/pulls/%(prid)s" % {
      "user"   : "psycofdj",
      "repo"   : "coverxygen",
      "prid"   : self.m_prid
    }

    try:
      print("GET %s" % l_url)
      l_req = requests.get(l_url, params=l_params, headers=l_headers)
    except BaseException as l_error:
      print("error while sending comment to github to %s : %s" % (l_url, str(l_error)))
      sys.exit(1)

    try:
      l_data = l_req.json()
      return l_data["head"]["sha"]
    except BaseException as l_error:
      print("error while reading sha from '%s' : %s" % (str(l_data), str(l_error)))
      sys.exit(1)

  def getTargetUrl(self):
    l_url = "https://travis-ci.org/psycofdj/coverxygen/builds/%(buildID)s"
    return l_url % {
      "buildID" : self.m_buildID
    }

  def make_badge(self, p_title, p_label, p_value, p_status, p_link = "#"):
    if p_status == "error":
      l_color = "red"
    elif p_status == "failure":
      l_color = "lightgrey"
    elif p_status == "warning":
      l_color = "yellow"
    else:
      l_color = "brightgreen"
    l_url = "https://img.shields.io/badge/%(label)s-%(value)s-%(color)s.svg" % {
      "label" : urllib.parse.quote(p_label),
      "value" : urllib.parse.quote(p_value),
      "color" : l_color
    }

    return "[![%(title)s](%(url)s)](%(link)s)" % {
      "title" : p_title,
      "url"   : l_url,
      "link"  : p_link
    }

  def comment_pr(self, p_body):
    if self.m_dryrun:
      return {}

    l_params  = { "access_token" : self.m_token }
    l_headers = { "Content-Type" : "application/json" }
    l_url     = "https://api.github.com/repos/%(user)s/%(repo)s/issues/%(prid)s/comments" % {
      "user"   : "psycofdj",
      "repo"   : "coverxygen",
      "prid"   : self.m_prid
    }
    l_data = {
      "body" : p_body
    }

    try:
      print("POST %s" % l_url)
      l_req = requests.post(l_url, params=l_params, headers=l_headers, data=json.dumps(l_data))
    except BaseException as l_error:
      print("error while sending comment to github")
      print(str(l_error))
      sys.exit(1)
    return l_req.json()

  def comment_commit(self, p_body):
    if self.m_dryrun:
      return {}

    l_params  = { "access_token" : self.m_token }
    l_headers = { "Content-Type" : "application/json" }
    l_url     = "https://api.github.com/repos/%(user)s/%(repo)s/commits/%(commitID)s/comments" % {
      "user"     : "psycofdj",
      "repo"     : "coverxygen",
      "commitID" : self.m_commit
    }
    l_data = {
      "body" : p_body
    }
    try:
      print("POST %s" % l_url)
      l_req = requests.post(l_url, params=l_params, headers=l_headers, data=json.dumps(l_data))
    except BaseException as l_error:
      print("error while seding comment to github")
      print(str(l_error))
      sys.exit(1)
    return l_req.json()


  def send_status(self, p_status, p_tag, p_description):
    if self.m_dryrun:
      return {}
    l_url    = "https://api.github.com/repos/%(user)s/%(repo)s/statuses/%(commit)s" % {
      "user"   : "psycofdj",
      "repo"   : "coverxygen",
      "commit" : self.m_commit
    }
    l_params  = { "access_token" : self.m_token }
    l_headers = { "Content-Type" : "application/json" }
    l_data    = {
      "state"       : p_status,
      "target_url"  : self.getTargetUrl(),
      "description" : p_description,
      "context"     : p_tag
    }

    try:
      print("POST %s" % l_url)
      l_req = requests.post(l_url, params=l_params, headers=l_headers, data=json.dumps(l_data))
    except BaseException as l_error:
      print("error while seding comment to github")
      print(str(l_error))
      sys.exit(1)
    return l_req.json()

  def run_unittests(self):
    print("-------------------")
    print("Running test suites")
    print("-------------------")

    l_proc = subprocess.Popen(["python3", "./devtools/unittests.py", "--format", "json", "-v"], stdout=subprocess.PIPE)
    l_proc.wait()
    try:
      l_lines = l_proc.stdout.read().decode("utf-8")
      l_data = json.loads(l_lines)
      l_info = {
        "nbtests" : l_data["tests"],
        "nbok"    : l_data["success"],
        "nbko"    : l_data["tests"] - l_data["success"]
      }
      l_description = "Ran %(nbtests)d tests : %(nbok)d success, %(nbko)d errors" % l_info
      l_status = "error"

      if l_info["nbko"] == 0:
        l_status = "success"
      for c_test in l_data["details"]["success"]:
        print("oK : %(file)s:%(class)s:%(method)s" % c_test)
      for c_test in l_data["details"]["errors"]:
        print("Ko : %(file)s:%(class)s:%(method)s : %(message)s" % c_test)
      for c_test in l_data["details"]["failures"]:
        print("Ko : %(file)s:%(class)s:%(method)s : %(message)s" % c_test)
      for c_test in l_data["details"]["expectedFailures"]:
        print("Ko : %(file)s:%(class)s:%(method)s : %(message)s" % c_test)
      for c_test in l_data["details"]["unexpectedSuccesses"]:
        print("Ko : %(file)s:%(class)s:%(method)s" % c_test)
      print("")
      print("Ran %(nbtests)d tests, %(nbok)d success, %(nbko)d failures" % l_info)
      l_badge = self.make_badge("Unit Tests", "unittests", "%(nbok)d / %(nbtests)d" % l_info, l_status)
      self.m_comment += "%s\n" % l_badge
    except Exception as l_error:
      l_status      = "failure"
      l_description = "unexpected error while reading unittests results"
      l_badge       = self.make_badge("Unit Tests", "unittests", "failure", l_status)
      self.m_comment += "%s\n" % l_badge
      print("error while running unittests : %s" % (l_error))
    self.send_status(l_status, "checks/unittests", l_description)
    print("")

  def run_pylint(self):
    print("-------------------")
    print("Running pylint     ")
    print("-------------------")

    l_proc = subprocess.Popen(["python3", "./devtools/xtdlint.py", "--rcfile", ".pylintrc", "-j", "4", "coverxygen", "-r", "yes", "-s", "yes" ], stdout=subprocess.PIPE)
    l_proc.wait()
    try:
      l_lines      = l_proc.stdout.read().decode("utf-8")
      l_data       = json.loads(l_lines)
      l_score      = l_data["report"]["score"]
      l_nbErrors   = l_data["report"]["errors"]["by_cat"].get("fatal", 0)
      l_nbErrors  += l_data["report"]["errors"]["by_cat"].get("error", 0)

      if l_score < 9:
        l_status = "error"
        l_description = "pylint score %.2f/10 too low" % l_score
      elif l_nbErrors != 0:
        l_status = "error"
        l_description = "pylint detected '%d' unacceptables errors" % l_nbErrors
      else:
        l_status = "success"
        l_description = "pylint score is %.2f/10" % l_score
      for c_module, c_data in l_data["errors"].items():
        for c_msg in c_data["items"]:
          c_msg["path"] = c_data["path"]
          print("%(C)s:%(symbol)-20s %(path)s:%(line)d:%(column)d " % c_msg)
      print("")
      print("Final score : %.2f/10" % l_score)
      l_badge = self.make_badge("PyLint", "pylint", "%.2f" % l_score, l_status)
      self.m_comment += "%s\n" % l_badge
    except Exception as l_error:
      l_status      = "failure"
      l_description = "unexpected error while reading pylint results"
      print("error while running pylint : %s" % (l_error))
      l_badge = self.make_badge("PyLint", "pylint", "failure", l_status)
      self.m_comment += "%s\n" % l_badge
    self.send_status(l_status, "checks/pylint", l_description)
    print("")

  def run_sphinx(self):
    print("------------------------")
    print("Genrating documentation ")
    print("------------------------")

    l_proc = subprocess.Popen(["sphinx-build", "-qaNW", "-b", "html", "-d", "../build/docs/cache", ".", "../build/docs/html" ], cwd="./docs", stderr=subprocess.PIPE)
    l_proc.wait()
    if l_proc.returncode != 0:
      l_status      = "error"
      l_description = "error while generating documentation"
      l_badge = self.make_badge("Documentation", "doc", "failed", l_status)
      self.m_comment += "%s\n" % l_badge
    else:
      l_status      = "success"
      l_description = "documentation successfully generated"
      l_badge = self.make_badge("Documentation", "doc", "passed", l_status)
      self.m_comment += "%s\n" % l_badge

    l_lines = l_proc.stderr.readlines()
    if len(l_lines):
      for c_line in l_lines:
        print(c_line.decode("utf-8"))
    else:
      print("")
      print("Documentation OK")

    self.send_status(l_status, "checks/documentation", l_description)
    print("")


  def run(self):
    if self.m_prid != "false" :
      self.m_commit = self.get_pr_commit()

    self.send_status("pending", "checks/unittests",     "running unittests...")
    self.send_status("pending", "checks/pylint",        "running pylint...")
    #self.send_status("pending", "checks/documentation", "running sphinx...")
    self.run_unittests()
    self.run_pylint()
    #self.run_sphinx()

    self.comment_commit("Automatic build report for commit %(commit)s:\n\n%(results)s" % {
      "commit" : self.m_commit,
      "results" : self.m_comment
    })
    # if self.m_prid != "false" :
    #   self.comment_pr("Automatic build report for commit %(commit)s:\n\n%(results)s" % {
    #     "commit" : self.m_commit,
    #     "results" : self.m_comment
    #   })

if __name__ == "__main__":
  l_app = StatusHelper()
  l_app.run()
