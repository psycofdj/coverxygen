;;; Directory Local Variables
;;; For more information see (info "(emacs) Directory Variables")

((nil . ((eval . (setq xtdmacs-code-python-test-bin-path
                       (concat
                        (file-name-directory
                         (let ((d (dir-locals-find-file ".")))
                           (if (stringp d) d (car d))))
                        "devtools/unittests.py"
                        ))))))
