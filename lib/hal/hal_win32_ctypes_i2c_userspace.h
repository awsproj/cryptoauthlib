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

#ifndef HAL_WIN32_CTYPES_I2C_USERSPACE_H_
#define HAL_WIN32_CTYPES_I2C_USERSPACE_H_

/** \defgroup hal_ Hardware abstraction layer (hal_)
 *
 * \brief
 * These methods define the hardware abstraction layer for communicating with a CryptoAuth device
 *
   @{ */

#define MAX_I2C_BUSES   2   // Raspberry Pi has 2 TWI

// A structure to hold I2C information
typedef struct atcaI2Cmaster
{
    uint8_t bus_no;
    uint8_t slave_addr;
    //char i2c_file[16];
    int  ref_ct;
} ATCAI2CMaster_t;


/* debug logger */
#define logdbg(...) do{printf("DBG %s ", __func__);printf("" __VA_ARGS__ );}while(0)
//#define logdbg(...) do{;}while(0)
#define logwarn(...) do{fprintf(stderr, "WARN %s ", __func__);\
                        fprintf(stderr, "" __VA_ARGS__ );}while(0)


/* interface function selector */
//#define WIN32_CTYPES_FUNC_WAKE  (1)
//#define WIN32_CTYPES_FUNC_IDLE  (2)
//#define WIN32_CTYPES_FUNC_SLEEP (3)
#define WIN32_CTYPES_FUNC_SEND  (4)
#define WIN32_CTYPES_FUNC_RECV  (5)


/* interface function data */
typedef struct Win32CtypesIfaceData_s
{
    uint32_t req_seqn;
    uint16_t data_len_in;
    uint16_t data_len_out;
    uint8_t  buf[256];
} Win32CtypesIfaceData_t;


/* local functions prototype */
extern ATCA_STATUS hal_win32_ctypes_register_cb( int (*callback)(uint32_t, uint32_t, uint32_t) );
extern ATCA_STATUS hal_win32_ctypes_get_request(uint32_t seqn, Win32CtypesIfaceData_t *data);
extern ATCA_STATUS hal_win32_ctypes_put_response(uint32_t seqn, Win32CtypesIfaceData_t *data);

extern ATCA_STATUS hal_i2c_discover_buses(int i2c_buses[], int max_buses); /* unimpl */
extern ATCA_STATUS hal_i2c_discover_devices(int bus_num, ATCAIfaceCfg cfg[], int *found); /* unimpl */
extern ATCA_STATUS hal_i2c_init(ATCAIface iface, ATCAIfaceCfg* cfg);
extern ATCA_STATUS hal_i2c_post_init(ATCAIface iface); /* empty */
extern ATCA_STATUS hal_i2c_send(ATCAIface iface, uint8_t address, uint8_t *txdata, int txlength);
extern ATCA_STATUS hal_i2c_receive(ATCAIface iface, uint8_t address, uint8_t *rxdata, uint16_t *rxlength);
extern void change_i2c_speed(ATCAIface iface, uint32_t speed); /* empty */
extern ATCA_STATUS hal_i2c_wake(ATCAIface iface);
extern ATCA_STATUS hal_i2c_idle(ATCAIface iface);
extern ATCA_STATUS hal_i2c_sleep(ATCAIface iface);
extern ATCA_STATUS hal_i2c_release(void *hal_data);


/** @} */

#endif /* HAL_WIN32_CTYPES_I2C_USERSPACE_H_ */

