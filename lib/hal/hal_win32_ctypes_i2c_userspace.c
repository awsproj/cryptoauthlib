/**
 * \file
 * \brief ATCA Hardware abstraction layer for Linux using I2C.
 *
 * \copyright (c) 2015-2020 Microchip Technology Inc. and its subsidiaries.
 *
 * \page License
 *
 * Subject to your compliance with these terms, you may use Microchip software
 * and any derivatives exclusively with Microchip products. It is your
 * responsibility to comply with third party license terms applicable to your
 * use of third party software (including open source software) that may
 * accompany Microchip software.
 *
 * THIS SOFTWARE IS SUPPLIED BY MICROCHIP "AS IS". NO WARRANTIES, WHETHER
 * EXPRESS, IMPLIED OR STATUTORY, APPLY TO THIS SOFTWARE, INCLUDING ANY IMPLIED
 * WARRANTIES OF NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A
 * PARTICULAR PURPOSE. IN NO EVENT WILL MICROCHIP BE LIABLE FOR ANY INDIRECT,
 * SPECIAL, PUNITIVE, INCIDENTAL OR CONSEQUENTIAL LOSS, DAMAGE, COST OR EXPENSE
 * OF ANY KIND WHATSOEVER RELATED TO THE SOFTWARE, HOWEVER CAUSED, EVEN IF
 * MICROCHIP HAS BEEN ADVISED OF THE POSSIBILITY OR THE DAMAGES ARE
 * FORESEEABLE. TO THE FULLEST EXTENT ALLOWED BY LAW, MICROCHIP'S TOTAL
 * LIABILITY ON ALL CLAIMS IN ANY WAY RELATED TO THIS SOFTWARE WILL NOT EXCEED
 * THE AMOUNT OF FEES, IF ANY, THAT YOU HAVE PAID DIRECTLY TO MICROCHIP FOR
 * THIS SOFTWARE.
 */

#include <cryptoauthlib.h>

///#include <linux/i2c-dev.h>
///#include <unistd.h>
///#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/stat.h>
///#include <fcntl.h>
#include <errno.h>
#include <string.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "atca_hal.h"
#include "hal_win32_ctypes_i2c_userspace.h"

#if 1 /* mock functions and macros to make it build */
#define open(x1,x2)     (1)
#define O_RDWR          (2)
#define ioctl(x1,x2,x3) (3)
#define I2C_SLAVE       (4)
#define write(x1,x2,x3) (5)
#define close(x)        (6)
#define read(x1,x2,x3)  (7)


static uint32_t win32_ctypes_req_seqn = 0; /* avoid 0 */
#define INC_SEQN do{if(++win32_ctypes_req_seqn ==0)win32_ctypes_req_seqn++;}while(0)

static Win32CtypesIfaceData_t win32_ctypes_req_resp_data;

static int (*win32_ctypes__callback_funcp)(uint32_t, uint32_t, uint32_t) = NULL;


ATCA_STATUS hal_win32_ctypes_register_cb( int (*callback)(uint32_t, uint32_t, uint32_t) )
{
    ATCA_STATUS rstatus = ATCA_GEN_FAIL;
    logdbg("\n");
    do {
        if ( callback == NULL ) {
            rstatus = ATCA_BAD_PARAM;
            break;
        }
        if ( win32_ctypes__callback_funcp != NULL ) {
            rstatus = ATCA_ALLOC_FAILURE;
            break;
        }
        win32_ctypes__callback_funcp = callback;
        rstatus = ATCA_SUCCESS;
    } while(0);
    logdbg(" rstatus %d\n", rstatus);
    return rstatus;
}

ATCA_STATUS hal_win32_ctypes_get_request(uint32_t seqn, Win32CtypesIfaceData_t *data)
{
    ATCA_STATUS rstatus = ATCA_GEN_FAIL;
    logdbg("\n");
    if ( data == NULL ) {
        rstatus = ATCA_BAD_PARAM;
    } else if ( seqn != 0 && seqn == win32_ctypes_req_resp_data.req_seqn ) {
        memcpy(data, &win32_ctypes_req_resp_data, sizeof(win32_ctypes_req_resp_data));
        rstatus = ATCA_SUCCESS;
    }
    logdbg(" rstatus %d\n", rstatus);
    return rstatus;
}

ATCA_STATUS hal_win32_ctypes_put_response(uint32_t seqn, Win32CtypesIfaceData_t *data)
{
    ATCA_STATUS rstatus = ATCA_GEN_FAIL;
    logdbg("\n");
    if ( data == NULL ) {
        rstatus = ATCA_BAD_PARAM;
    } else if ( seqn != 0 && seqn == win32_ctypes_req_resp_data.req_seqn ) {
        memcpy(&win32_ctypes_req_resp_data, data, sizeof(win32_ctypes_req_resp_data));
        rstatus = ATCA_SUCCESS;
    }
    logdbg(" rstatus %d\n", rstatus);
    return rstatus;
}
#endif


/** \defgroup hal_ Hardware abstraction layer (hal_)
 *
 * \brief
 * These methods define the hardware abstraction layer for communicating with a CryptoAuth device
 *
   @{ */

typedef struct atca_i2c_host_s
{
    char i2c_file[16];
    int  ref_ct;
} atca_i2c_host_t;

/** \brief HAL implementation of I2C init
 *
 * this implementation assumes I2C peripheral has been enabled by user. It only initialize an
 * I2C interface using given config.
 *
 *  \param[in] hal pointer to HAL specific data that is maintained by this HAL
 *  \param[in] cfg pointer to HAL specific configuration data that is used to initialize this HAL
 * \return ATCA_SUCCESS on success, otherwise an error code.
 */

ATCA_STATUS hal_i2c_init(ATCAIface iface, ATCAIfaceCfg* cfg)
{
    ATCA_STATUS ret = ATCA_BAD_PARAM;
logdbg("\n");

    if (!iface || !cfg)
    {
        return ret;
    }

    if (iface->hal_data)
    {
        atca_i2c_host_t * hal_data = (atca_i2c_host_t*)iface->hal_data;

        // Assume the bus had already been initialized
        hal_data->ref_ct++;

        ret = ATCA_SUCCESS;
    }
    else
    {
        atca_i2c_host_t * hal_data = malloc(sizeof(atca_i2c_host_t));
        int bus = cfg->atcai2c.bus; // 0-based logical bus number
logdbg("HAL dump:  i2c  bus %d  slave_address %u\n", bus, 1234/*cfg->atcai2c.slave_address*/);

        if (hal_data)
        {
            hal_data->ref_ct = 1;  // buses are shared, this is the first instance

            (void)snprintf(hal_data->i2c_file, sizeof(hal_data->i2c_file) - 1, "/dev/i2c-%d", bus);

            iface->hal_data = hal_data;

            ret = ATCA_SUCCESS;
        }
        else
        {
            ret = ATCA_ALLOC_FAILURE;
        }
    }

    return ret;

}

/** \brief HAL implementation of I2C post init
 * \param[in] iface  instance
 * \return ATCA_SUCCESS on success, otherwise an error code.
 */
ATCA_STATUS hal_i2c_post_init(ATCAIface iface)
{
    ((void)iface);
    return ATCA_SUCCESS;
}

/** \brief HAL implementation of I2C send
 * \param[in] iface         instance
 * \param[in] word_address  device transaction type
 * \param[in] txdata        pointer to space to bytes to send
 * \param[in] txlength      number of bytes to send
 * \return ATCA_SUCCESS on success, otherwise an error code.
 */

ATCA_STATUS hal_i2c_send(ATCAIface iface, uint8_t address, uint8_t *txdata, int txlength)
{
logdbg("\n");
    atca_i2c_host_t * hal_data = (atca_i2c_host_t*)atgetifacehaldat(iface);
    int f_i2c;  // I2C file descriptor

    if (!hal_data)
    {
        return ATCA_NOT_INITIALIZED;
    }

    #if 0
    // Initiate I2C communication
    if ( (f_i2c = open(hal_data->i2c_file, O_RDWR)) < 0)
    {
        return ATCA_COMM_FAIL;
    }

    // Set Device Address
    if (ioctl(f_i2c, I2C_SLAVE, address >> 1) < 0)
    {
        close(f_i2c);
        return ATCA_COMM_FAIL;
    }

    // Send data
    if (write(f_i2c, txdata, txlength) != txlength)
    {
        close(f_i2c);
        return ATCA_COMM_FAIL;
    }

    close(f_i2c);
    return ATCA_SUCCESS;
    #endif
    ATCA_STATUS rstatus = ATCA_GEN_FAIL; // unspecified error
    INC_SEQN;
    if ( win32_ctypes__callback_funcp == NULL ) {
        rstatus = ATCA_COMM_FAIL;
        logwarn(" Error: win32_ctypes__callback_funcp null\n");
    } else if (txlength <= 0 || txlength >= sizeof(win32_ctypes_req_resp_data.buf) ) {
        rstatus = ATCA_BAD_PARAM;
        logwarn(" Error: txlength %d out of range\n", txlength);
    } else {
        memset(&win32_ctypes_req_resp_data, 0, sizeof(win32_ctypes_req_resp_data));
        win32_ctypes_req_resp_data.req_seqn = win32_ctypes_req_seqn;
        memcpy(win32_ctypes_req_resp_data.buf, txdata, (uint32_t)txlength);
        win32_ctypes_req_resp_data.data_len_in = (uint16_t)txlength;
        logdbg("  calling callback function \n");
        int r1 = (*win32_ctypes__callback_funcp)(WIN32_CTYPES_FUNC_SEND,
                                                 win32_ctypes_req_seqn, (uint32_t)txlength);
        logdbg("  returned from callback function r1 %d\n", r1);
        if ( r1 != ATCA_SUCCESS ) {
            rstatus = r1;
            logwarn(" status %d\n", rstatus);
        } else if ( win32_ctypes_req_resp_data.req_seqn != win32_ctypes_req_seqn ) {
            rstatus = ATCA_COMM_FAIL;
            logwarn(" status %d due to seqn mismatch\n", rstatus);
        } else {
            rstatus = ATCA_SUCCESS;
            logdbg(" status %d\n", rstatus);
        }
    }

    return rstatus;
}

/** \brief HAL implementation of I2C receive function
 * \param[in]    iface          Device to interact with.
 * \param[in]    address        device address
 * \param[out]   rxdata         Data received will be returned here.
 * \param[in,out] rxlength      As input, the size of the rxdata buffer.
 *                              As output, the number of bytes received.
 * \return ATCA_SUCCESS on success, otherwise an error code.
 */
ATCA_STATUS hal_i2c_receive(ATCAIface iface, uint8_t address, uint8_t *rxdata, uint16_t *rxlength)
{
logdbg("\n");
    atca_i2c_host_t * hal_data = (atca_i2c_host_t*)atgetifacehaldat(iface);
    int f_i2c;  // I2C file descriptor

    if (!hal_data)
    {
        return ATCA_NOT_INITIALIZED;
    }

    #if 0
    // Initiate I2C communication
    if ( (f_i2c = open(hal_data->i2c_file, O_RDWR)) < 0)
    {
        return ATCA_COMM_FAIL;
    }

    // Set Device Address
    if (ioctl(f_i2c, I2C_SLAVE, address >> 1) < 0)
    {
        close(f_i2c);
        return ATCA_COMM_FAIL;
    }

    if (read(f_i2c, rxdata, *rxlength) != *rxlength)
    {
        close(f_i2c);
        return ATCA_COMM_FAIL;
    }

    close(f_i2c);
    return ATCA_SUCCESS;
    #endif

    ATCA_STATUS rstatus = ATCA_GEN_FAIL; // unspecified error
    INC_SEQN;
    uint16_t rxdata_max_size = *rxlength;

    if ( win32_ctypes__callback_funcp == NULL ) {
        rstatus = ATCA_COMM_FAIL;
        logwarn(" Error: win32_ctypes__callback_funcp null\n");
    } else if (rxdata_max_size >= sizeof(win32_ctypes_req_resp_data.buf) ) {
        rstatus = ATCA_BAD_PARAM;
        logwarn(" Error: rxlength %d out of range\n", rxdata_max_size);
    } else {
        memset(&win32_ctypes_req_resp_data, 0, sizeof(win32_ctypes_req_resp_data));
        win32_ctypes_req_resp_data.req_seqn = win32_ctypes_req_seqn;
        win32_ctypes_req_resp_data.data_len_in = (uint16_t)rxdata_max_size;
        logdbg("  calling callback function \n");
        int r1 = (*win32_ctypes__callback_funcp)(WIN32_CTYPES_FUNC_RECV,
                                                 win32_ctypes_req_seqn, (uint32_t)rxdata_max_size);
        logdbg("  returned from callback function r1 %d\n", r1);
        if ( r1 != ATCA_SUCCESS ) {
            rstatus = r1;
            logwarn(" status %d\n", rstatus);
        } else if ( win32_ctypes_req_resp_data.req_seqn != win32_ctypes_req_seqn ) {
            rstatus = ATCA_COMM_FAIL;
            logwarn(" status %d due to seqn mismatch\n", rstatus);
        } else {
            uint32_t dlen = win32_ctypes_req_resp_data.data_len_out;
            if ( dlen < 1 || dlen >= sizeof(win32_ctypes_req_resp_data.buf) ) {
                rstatus = ATCA_COMM_FAIL;
                //logwarn(" status %d due to rxlength %u invalid\n", rstatus, dlen);
                logdbg(" status %d\n", rstatus);
            } else if ( dlen > rxdata_max_size ) {
                rstatus = ATCA_COMM_FAIL;
                logwarn(" status %d due to rxlength %u overflow %u\n", rstatus, dlen,
                            rxdata_max_size);
            } else if ( dlen != win32_ctypes_req_resp_data.buf[0] ) {
                rstatus = ATCA_COMM_FAIL;
                logwarn(" status %d due to rxlength %u mismatch data[0] %u\n", rstatus, dlen,
                            win32_ctypes_req_resp_data.buf[0]);
            } else {
                memcpy(rxdata, win32_ctypes_req_resp_data.buf, dlen);
                *rxlength = dlen;
                rstatus = ATCA_SUCCESS;
                logdbg(" status %d\n", rstatus);
            }
        }
    }

    return rstatus;
}

/** \brief Perform control operations for the kit protocol
 * \param[in]     iface          Interface to interact with.
 * \param[in]     option         Control parameter identifier
 * \param[in]     param          Optional pointer to parameter value
 * \param[in]     paramlen       Length of the parameter
 * \return ATCA_SUCCESS on success, otherwise an error code.
 */
ATCA_STATUS hal_i2c_control(ATCAIface iface, uint8_t option, void* param, size_t paramlen)
{
    (void)option;
    (void)param;
    (void)paramlen;

    if (iface && iface->mIfaceCFG)
    {
        /* This HAL does not support any of the control functions */
        return ATCA_UNIMPLEMENTED;
    }
    return ATCA_BAD_PARAM;
}

/** \brief manages reference count on given bus and releases resource if no more refences exist
 * \param[in] hal_data - opaque pointer to hal data structure - known only to the HAL implementation
 * \return ATCA_SUCCESS on success, otherwise an error code.
 */

ATCA_STATUS hal_i2c_release(void *hal_data)
{
logdbg("\n");
    atca_i2c_host_t *hal = (atca_i2c_host_t*)hal_data;

    // if the use count for this bus has gone to 0 references, disable it.  protect against an unbracketed release
    if (hal && --(hal->ref_ct) <= 0)
    {
        free(hal);
    }

    return ATCA_SUCCESS;
}

/** @} */
