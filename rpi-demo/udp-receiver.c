#include "flipdot.h"
#include "flipdot_net.h"
#include <stdio.h>
#include <stdbool.h>

int main(void)
{
    
    bool init = false;
    flipdot_net_init();
    
    uint8_t data[(16*80)/8];
    while (1) {
        int n = flipdot_net_recv_frame((uint8_t *)data, sizeof(data));
        if(!init) {
            init=true;
            flipdot_init();
        }
        
        printf("got %u bytes\n", n);
        if(n >= sizeof(data)) {
            flipdot_data(data, sizeof(data));
            n -=  sizeof(data);
        } else {
            flipdot_data(data, n);
        }
    }
    return 0;
}
