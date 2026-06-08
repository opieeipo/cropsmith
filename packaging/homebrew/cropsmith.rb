class Cropsmith < Formula
  include Language::Python::Virtualenv

  desc "Cross-platform Swiss Army knife for document and media manipulation"
  homepage "https://github.com/opieeipo/cropsmith"
  url "https://github.com/opieeipo/cropsmith/archive/refs/tags/v0.2.0.tar.gz"
  sha256 "561c14ff556126645160a1b81542dacef5b5e6b2d3363a3cd3fd6ce9e3fb8727"
  license "MIT"

  depends_on "python@3.12"
  depends_on "ffmpeg"
  depends_on "ghostscript"
  depends_on "tesseract"

  # NOTE: This formula is NOT currently installable as-is.
  #
  # Homebrew builds from source, so every Python dependency must be vendored as
  # a `resource` (sdist). `pdf2docx` pulls in `opencv-python-headless`, which
  # publishes wheels ONLY -- no source distribution -- so it cannot be vendored:
  #
  #   $ brew update-python-resources Formula/cropsmith.rb
  #   Error: opencv-python-headless exists on PyPI but lacks a suitable
  #          source distribution
  #
  # Recommended install path on macOS/Linux is pipx (see packaging/README.md):
  #
  #   pipx install cropsmith
  #
  # To make a real Homebrew formula viable, move `pdf2docx` (the opencv source)
  # into an optional extra so the base install is opencv-free, then run
  # `brew update-python-resources` to populate the stanzas below.
  #
  # <<< resources go here >>>

  def install
    virtualenv_install_with_resources
  end

  def caveats
    <<~EOS
      Web capture (web-to-pdf) needs the Chromium browser used by Playwright.
      After installing, run once:

        #{opt_libexec}/bin/playwright install chromium
    EOS
  end

  test do
    assert_match "Cropsmith", shell_output("#{bin}/cropsmith --help")
  end
end
