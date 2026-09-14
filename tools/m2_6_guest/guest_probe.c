/* AmiSandbox M2.6 guest-side bootstrap.
 *
 * AROS reliably executes the first external command in the qualification
 * Startup-Sequence, while starting a second external helper has proven
 * unreliable in CI.  Keep the qualification fail-closed by having the first
 * guest process perform the complete guest-originated media mutation and
 * witness write itself.  All writes remain confined to DF0:.
 */
#include <stdio.h>

static const unsigned char marker[] =
    "AMISANDBOX-M2.6-GUEST-WRITE";

static void write_stage(const char *stage)
{
    FILE *f = fopen("DF0:M2_6_STAGE", "wb");
    if (f == NULL)
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

    f = fopen("DF0:M2_6_BOOTED", "wb");
    if (f == NULL)
        return 20;
    if (fputs("startup-sequence reached guest executable\n", f) < 0) {
        fclose(f);
        return 20;
    }
    if (fclose(f) != 0)
        return 20;

    write_stage("guest-bootstrap-started");

    f = fopen("DF0:M2_6_OFFSET", "rb");
    if (f == NULL) {
        write_stage("offset-open-failed");
        return 19;
    }
    n = fread(offset, 1, sizeof(offset) - 1, f);
    fclose(f);
    if (n == 0) {
        write_stage("offset-read-failed");
        return 19;
    }
    while (n && (offset[n - 1] == '\n' || offset[n - 1] == '\r'))
        --n;
    offset[n] = 0;
    write_stage("offset-read");

    f = fopen("DF0:M2_6_MARKER", "r+b");
    if (f == NULL) {
        write_stage("marker-open-failed");
        return 20;
    }
    if (fwrite(marker, 1, sizeof(marker) - 1, f) != sizeof(marker) - 1) {
        fclose(f);
        write_stage("marker-write-failed");
        return 20;
    }
    if (fclose(f) != 0) {
        write_stage("marker-close-failed");
        return 20;
    }
    write_stage("marker-written");

    f = fopen("DF0:M2_6_WITNESS.JSON", "wb");
    if (f == NULL) {
        write_stage("witness-open-failed");
        return 21;
    }
    if (fprintf(f,
        "{\"schema_version\":1,"
        "\"amisandbox_milestone\":\"m2.6\","
        "\"mutation_origin\":\"guest\","
        "\"mechanism\":\"guest-program\","
        "\"offset\":%s,"
        "\"marker_hex\":\"414d4953414e44424f582d4d322e362d47554553542d5752495445\"}\n",
        offset) < 0) {
        fclose(f);
        write_stage("witness-write-failed");
        return 21;
    }
    if (fclose(f) != 0) {
        write_stage("witness-close-failed");
        return 21;
    }

    write_stage("witness-written");
    return 0;
}
