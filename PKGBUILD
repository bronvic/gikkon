# Maintainer: Voronwe Sul <Voronwe.S@protonmail.com>
# Contributor: Voronwe Sul <Voronwe.S@protonmail.com>

pkgname="gikkon"
pkgver="0.1.0"
pkgrel=1
pkgdesc="Backup tool for configs, which uses git as storage"
arch=("any")
url="https://github.com/bronvic/$pkgname"
license=("MIT")
depends=("python>=3.7.0")
source=("$url/archive/refs/tags/$pkgname-$pkgver.tar.gz")
sha256sums=("SKIP")

build() {
    cd "$srcdir/$pkgname-$pkgver"
    make build
}

package() {
    cd "$srcdir/$pkgname-$pkgver"
    make install
}
