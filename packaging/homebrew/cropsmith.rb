class Cropsmith < Formula
  include Language::Python::Virtualenv

  desc "Cross-platform Swiss Army knife for document and media manipulation"
  homepage "https://github.com/opieeipo/cropsmith"
  url "https://github.com/opieeipo/cropsmith/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "4443927d60ea22de3593f495be0bec0a11a668899197a259b01d75f5c21239fb"
  license "MIT"

  depends_on "python@3.12"
  depends_on "ffmpeg"
  depends_on "ghostscript"
  depends_on "tesseract"

  # Python dependencies are vendored as `resource` blocks so the build is
  # network-free (a Homebrew requirement). Generate / refresh them with:
  #
  #   brew update-python-resources Formula/cropsmith.rb
  #
  # That command reads pyproject.toml and writes one `resource` stanza per
  # transitive dependency (click, playwright, pypdf, pdf2docx, pytesseract,
  # Pillow, PyMuPDF, ...). Until it has been run at least once, `brew install`
  # from this formula will fail to resolve dependencies. See packaging/README.md.
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
