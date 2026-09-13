/* AmiSandbox M2.6 guest-side removable-media writer.
 *
 * This program must execute inside the emulated Amiga.  It performs two
 * AmigaDOS writes to DF0:: a deterministic binary marker and a JSON witness.
 * The host-side qualification may verify and extract these artifacts, but it
 * must never create them.
 */

#include <dos/dos.h>
#include <proto/dos.h>

static const unsigned char marker[] = {
    0x41, 0x4d, 0x49, 0x53, 0x41, 0x4e, 0x44, 0x42,
    0x4f, 0x58, 0x2d, 0x4d, 0x32, 0x2e, 0x36, 0x2d,
    0x47, 0x55, 0x45, 0x53, 0x54, 0x2d, 0x57, 0x52,
    0x49, 0x54, 0x45
};

static const char witness[] =
    "{\"schema_version\":1,"
    "\"amisandbox_milestone\":\"m2.6\","
    "\"mutation_origin\":\"guest\","
    "\"mechanism\":\"guest-program\","
    "\"logical_file\":\"DF0:M2_6_MARKER\","
    "\"logical_offset\":0,"
    "\"marker_hex\":\"414d4953414e44424f582d4d322e362d47554553542d5752495445\"}"
    "\n";

static int write_all(const char *path, const void *data, LONG size)
{
    BPTR fh = Open((STRPTR)path, MODE_NEWFILE);
    LONG written;

    if (!fh)
        return 0;

    written = Write(fh, (APTR)data, size);
    Close(fh);
    return written == size;
}

int main(void)
{
    if (!write_all("DF0:M2_6_MARKER", marker, (LONG)sizeof(marker)))
        return 20;
    if (!write_all("DF0:M2_6_WITNESS.JSON", witness, (LONG)(sizeof(witness) - 1)))
        return 21;

    /* Keep the guest alive briefly so the filesystem has time to flush the
     * writes before the qualification asks Amiberry to exit cleanly. */
    Delay(25);
    return 0;
}
