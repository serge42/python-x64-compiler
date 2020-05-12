#include <stdio.h>

int main(int argc, char **argv)
{
    long long x = 1, y;
    if (x > 0 && x < 100)
    {
        y = 1;
    } else 
    {
        y = 2;
    }
    printf("%lld\n", y);
    return 0;
}