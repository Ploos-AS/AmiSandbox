/* AmiSandbox M2.6 guest-side qualification helper.
 * Runs inside the emulated Amiga and writes only to DF0:.
 */
#include <stdio.h>
#include <string.h>

static const unsigned char marker[] =
    "AMISANDBOX-M2.6-GUEST-WRITE";

static void write_stage(const char *stage)
{
    FILE *f = fopen("DF0:M2_6_STAGE", "wb");
    if (!f)
        return;
    fputs(stage, f);
    fputc('\n', f);
    fclose(f);
}

int main(void)
{
    char offset[32];
    FILE *f;
    size_t n;

    write_stage("guestwrite-started");

    f = fopen("DF0:M2_6_OFFSET", "rb");
    if (!f) {
        write_stage("offset-open-failed");
        return 19;
    }
    n = fread(offset, 1, sizeof(offset) - 1, f);
    fclose(f);
    if (!n) {
        write_stage("offset-read-failed");
        return 19;
    }
    while (n && (offset[n - 1] == '\n' || offset[n - 1] == '\r'))
        --n;
    offset[n] = 0;
    write_stage("offset-read");

    f = fopen("DF0:M2_6_MARKER", "r+b");
    if (!f) {
        write_stage("marker-open-failed");
        return 20;
    }
    if (fwrite(marker, 1, sizeof(marker) - 1, f) != sizeof(marker) - 1) {
        fclose(f);
        write_stage("marker-write-failed");
        return 20;
    }
    fclose(f);
    write_stage("marker-written");

    f = fopen("DF0:M2_6_WITNESS.JSON", "wb");
    if (!f) {
        write_stage("witness-open-failed");
        return 21;
    }
    fprintf(f,
        "{\"schema_version\":1,"
        "\"amisandbox_milestone\":\"m2.6\","
        "\"mutation_origin\":\"guest\","
        "\"mechanism\":\"guest-program\","
        "\"offset\":%s,"
        "\"marker_hex\":\"414d4953414e44424f582d4d322e362d47554553542d5752495445\"}\n",
        offset);
    fclose(f);
    write_stage("witness-written");
    return 0;
}
