#include <stdio.h>

int main(void)
{
    FILE *f = fopen("DF0:M2_6_BOOTED", "wb");
    if (f == NULL) {
        return 20;
    }

    if (fputs("startup-sequence reached guest executable\n", f) < 0) {
        fclose(f);
        return 20;
    }

    if (fclose(f) != 0) {
        return 20;
    }

    return 0;
}
