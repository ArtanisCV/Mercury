#include <stdio.h>


double putchard(double c)
{
    putchar((char)c);
    return 0;
}

double printd(double n)
{
    printf("%f", n);
    return 0;
}

double flush()
{
    fflush(stdout);
    return 0;
}