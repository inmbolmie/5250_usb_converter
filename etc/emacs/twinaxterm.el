;;; Optional Emacs configuration for use with 5250_terminal.py

;; This configuration enhances the display by highlighting the mode
;; line using "magic cookie dough" attributes and using some non-ASCII
;; characters for e.g. wrapped lines.  The instructions below cover
;; applying all of the configuration, but if desired, individual
;; functions may be called from your ~/.emacs.

;;; Testing this out:

;; 1. Open this file in Emacs
;; 2. M-x eval-buffer RET
;; 3. M-x twinaxterm-configure-all RET
;;
;; Your mode line should be highlighted now.

;;; Applying this configuration automatically when GNU Emacs starts up:

;; Add the following to your ~/.emacs file, or if you don't have one,
;; create one with these contents:
;;
;;   (load "/PATH/TO/twinaxterm.el")
;;   (twinaxterm-maybe-configure-all)

;; TODO: Allow things like attributes and mode line right-hand padding
;; to be modified via `customize'.

;; "Magic cookie dough" characters
;;
;; Use \Uxxxxxxxx escapes instead of the literal Unicode characters so
;; that the attributes don't take effect while viewing this file.
(defconst twinaxterm-attribute-normal "\U000F5220")
(defconst twinaxterm-attribute-reverse "\U000F5221")
(defconst twinaxterm-attribute-intensity "\U000F5222")


(defun twinaxterm-mode-line-render ()
  "Render the mode line to a string according to
`twinaxterm-mode-line-format', then add the end attribute byte -
which must always be present - and return the result."
  (let* ((available-width (- (window-width) 1))
         ;; Is the window for which the mode line is being rendered is
         ;; the one which `eldoc-minibuffer-message' would have added
         ;; a mode line prefix to?
         (twinaxterm-is-eldoc-minibuffer
          (eq (selected-window)
              (or (window-in-direction 'above (minibuffer-window))
                  (minibuffer-selected-window)
                  (get-largest-window))))
         ;; Should `window-total-width' be overridden here as
         ;; well/instead?  Neither seems to really be necessary for
         ;; the default mode-line-format in GNU Emacs 28.2.
         (content (cl-letf ((window-width (lambda ()
                                                  available-width)))
                    (format-mode-line twinaxterm-mode-line-format))))
    (concat (string-replace
             "%" "%%" ; escape to prevent further processing
             (string-pad (truncate-string-to-width content available-width)
                         available-width ?-))
            twinaxterm-attribute-normal)))

(defun twinaxterm-configure-modeline ()
  "Modify `mode-line-format' so that it is wrapped in attribute
bytes.  This method is loosely based on
https://emacs.stackexchange.com/questions/5529"
  (interactive)

  (setq mode-line-front-space twinaxterm-attribute-reverse)
  ;; `format-mode-line' doesn't generate "infinitely many dashes" when
  ;; this contains "%-", so right-hand padding must be generated
  ;; explicitly by our rendering function.
  (setq mode-line-end-spaces "")

  ;; Don't re-capture mode-line-format if we've already modified it!
  (unless (boundp 'twinaxterm-mode-line-format)
    (setq twinaxterm-mode-line-format
          ;; Include the help text that `eldoc-minibuffer-message'
          ;; adds to the front of the modeline (e.g. after typing `M-:
          ;; (message') in the wrapped part of the message, otherwise
          ;; the end attribute cookie will be cut off.
          (list '(eldoc-mode-line-string
                  (twinaxterm-is-eldoc-minibuffer
                   ("" twinaxterm-attribute-intensity eldoc-mode-line-string)))
                mode-line-format)))

  (setq-default mode-line-format
                '(;; `eldoc-minibuffer-message' will modify this
                  ;; format if it doesn't find this here - naturally
                  ;; it doesn't know that this string is included in
                  ;; twinaxterm-mode-line-format.
                  (eldoc-mode-line-string "")
                  (:eval (twinaxterm-mode-line-render)))))

(defun twinaxterm-configure-display-table ()
  "Use some non-ASCII characters, which stand out a bit more, for
characters outside of the editing area."
  (interactive)
  (mapc (lambda (args)
          (apply 'set-display-table-slot standard-display-table args))
        (list (list 'truncation (make-glyph-code ?§ 'default))
              (list 'wrap (make-glyph-code ?¬ 'default))
              ;; This character is not available with some older
              ;; terminals.  Until there is some way for this code to
              ;; determine whether it is available, it is suggested
              ;; that you update the relevant
              ;; CUSTOM_CHARACTER_CONVERSIONS map in 5250_terminal.py
              ;; to map this character to the EBCDIC code for "|".
              (list 'vertical-border (make-glyph-code ?¦ 'default)))))

(defun twinaxterm-configure-all ()
  (interactive)
  (menu-bar-mode -1)
  (twinaxterm-configure-modeline)
  (twinaxterm-configure-display-table))

(defun twinaxterm-maybe-configure-all ()
  "Apply twinax terminal configuration if it appears that such a
terminal is in use, otherwise do nothing."
  (when (getenv "TWINAXTERM")
    (twinaxterm-configure-all)))
