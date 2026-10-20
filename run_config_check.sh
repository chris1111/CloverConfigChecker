#!/bin/bash
# ============================================================================
# CloverConfigChecker -- config.plist validation for Clover
# ============================================================================

CHECKER_ROOT="$(cd "$(dirname "$0")" && pwd)"

# Package search: next to this script (canonical vendored layout
# CloverPackage/CloverConfigChecker/), or one level up (dev tree).
PKG_PARENT=""
for d in "$CHECKER_ROOT" "$CHECKER_ROOT/.."; do
    if [ -d "$d/clover_config_checker" ]; then
        PKG_PARENT="$(cd "$d" && pwd)"
        break
    fi
done

# --- locate the config -----------------------------------------------------
CONFIG="${1:-${CLOVER_CONFIG:-}}"
if [ -z "$CONFIG" ]; then
    for cand in \
        "${CLOVER_PKG_DIR:-}/EFI/CLOVER/config-sample.plist" \
        "$CHECKER_ROOT/../CloverV2/EFI/CLOVER/config-sample.plist" \
        "$CHECKER_ROOT/CloverV2/EFI/CLOVER/config-sample.plist" \
        "${CLOVERROOT:-}/CloverPackage/CloverV2/EFI/CLOVER/config-sample.plist" \
        "$CHECKER_ROOT/config.plist"
    do
        if [ -f "$cand" ]; then CONFIG="$cand"; break; fi
    done
fi

# --- skip conditions -------------------------------------------------------
if [ -z "$PKG_PARENT" ]; then
    echo "CloverConfigChecker: clover_config_checker package not found next to $0 -- skipping config validation"
    exit 0
fi

PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
    echo "CloverConfigChecker: python3 not found -- skipping config validation"
    exit 0
fi

if [ -z "$CONFIG" ] || [ ! -f "$CONFIG" ]; then
    echo "CloverConfigChecker: no config.plist to validate -- skipping (pass a path as \$1 or set CLOVER_CONFIG)"
    exit 0
fi

# Make a relative $1 absolute BEFORE changing directory below, so the
# script works from ANY directory:  cd ~/Desktop && /path/to/run_config_check.sh config.plist
case "$CONFIG" in /*) ;; *) CONFIG="$(pwd)/$CONFIG" ;; esac

# --- report mode -----------------------------------------------------------
# Explicit config passed by the caller  -> MANUAL mode (the standard user
# report, same output as the CLI). Auto-detected config (no $1) or
# CHECKER_BUILD=1 -> build mode ("?"-documentation note suppressed).
if [ "${CHECKER_BUILD:-0}" = "1" ] || [ -z "${1:-}" ]; then
    BUILD_ARGS="--build"
else
    BUILD_ARGS=""
fi

# --- run -------------------------------------------------------------------
# FULL verified-section report by DEFAULT (banner + checklist + summary).
# Export CHECKER_QUIET=1 for the compact one-line output instead.
if [ "${CHECKER_QUIET:-0}" = "1" ]; then
    echo ""
    ( cd "$PKG_PARENT" && exec "$PY" -m clover_config_checker $BUILD_ARGS --oneline "$CONFIG" )
    rc=$?

    # --- verdict handling (quiet) ------------------------------------------
    if [ "$rc" -ne 0 ]; then
        if [ "${CHECKER_STRICT:-0}" = "1" ]; then
            echo "CloverConfigChecker: CHECKER_STRICT=1 is set -- failing the build"
            exit "$rc"
        fi
        echo "CloverConfigChecker: validation reported problems -- build continues (export CHECKER_STRICT=1 to fail the build)"
    fi
    exit 0
fi

echo ""
echo "=============================================================="
echo "  CloverConfigChecker -- validating config.plist"
echo "--------------------------------------------------------------"
echo "  config : $CONFIG"
echo "=============================================================="

( cd "$PKG_PARENT" && exec "$PY" -m clover_config_checker $BUILD_ARGS "$CONFIG" )
rc=$?

# --- verdict handling (full report) ----------------------------------------
if [ "$rc" -ne 0 ]; then
    if [ "${CHECKER_STRICT:-0}" = "1" ]; then
        echo "=============================================================="
        echo "  CloverConfigChecker: validation FAILED (exit $rc)"
        echo "  CHECKER_STRICT=1 is set -- failing the build."
        echo "=============================================================="
        exit "$rc"
    fi
    echo "=============================================================="
    echo "  CloverConfigChecker: validation reported problems (exit $rc)"
    echo "  Build continues. Set CHECKER_STRICT=1 to fail the build"
    echo "  when the shipped config does not validate."
    echo "=============================================================="
else
    echo "=============================================================="
    echo "  CloverConfigChecker: config.plist is valid -- all good!"
    echo "=============================================================="
fi
exit 0
