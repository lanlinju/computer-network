#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/*******************************************************************
 ALTERNATING BIT AND GO-BACK-N NETWORK EMULATOR: VERSION 1.1  J.F.Kurose
**********************************************************************/

/**
 * SR（Selective Repeat）协议 伪代码，每个分组应该各自维护一个独立的计时器，
 * 而不是像 Go-Back-N（GBN）那样只有一个全局定时器
 */

// todo: 定时器

#define BIDIRECTIONAL 0

extern float time;

struct msg {
    char data[20];
};

struct pkt {
    int seqnum;
    int acknum;
    int checksum;
    char payload[20];
};

void tolayer3(int AorB, struct pkt packet);
void tolayer5(int AorB, char datasent[20]);
void starttimer(int AorB, float increment);
void stoptimer(int AorB);

/********* STUDENTS WRITE THE NEXT SEVEN ROUTINES *********/

#define WINDOW_SIZE 4  /* SR窗口大小通常较小 */
#define MAX_SEQ 8      /* 序列号空间，至少是窗口大小的2倍 */
#define TIMEOUT_INTERVAL 600.0

/* 发送方数据结构 */
struct msg send_buffer[MAX_SEQ];
int send_base = 0;
int next_seq = 0;
int acked[MAX_SEQ] = {0};  /* 标记哪些分组已被确认 */
float timer_start[MAX_SEQ] = {0}; /* 每个分组的定时器开始时间 */

/* 接收方数据结构 */
struct msg recv_buffer[MAX_SEQ];
int recv_base = 0;
int received[MAX_SEQ] = {0}; /* 标记哪些分组已接收 */

/* 校验和计算 */
unsigned short compute_checksum(struct pkt* packet) {
    unsigned short* data = (unsigned short*)packet;
    int word_count = sizeof(struct pkt) / sizeof(unsigned short);
    unsigned int sum = 0;
    
    for (int i = 0; i < word_count; i++) {
        sum += data[i];
        if (sum & 0xFFFF0000) {
            sum &= 0xFFFF;
            sum++;
        }
    }
    
    return ~(sum & 0xFFFF);
}

int is_corrupt(struct pkt* packet) {
    return compute_checksum(packet) != packet->checksum;
}

/* 发送分组并启动定时器 */
void send_packet(int seq_num) {
    struct pkt packet;
    packet.seqnum = seq_num;
    packet.acknum = 0;
    strncpy(packet.payload, send_buffer[seq_num].data, 20);
    packet.checksum = compute_checksum(&packet);
    
    tolayer3(0, packet);
    printf("发送分组: seq=%d\n", seq_num);
    
    /* 启动该分组的定时器 */
    if (!acked[seq_num]) {
        starttimer(0, TIMEOUT_INTERVAL);
        timer_start[seq_num] = time; /* 记录发送时间 */
    }
}

/* 发送ACK */
void send_ack(int ack_num, int is_nak) {
    struct pkt ack_packet;
    ack_packet.seqnum = 0;
    ack_packet.acknum = ack_num;
    ack_packet.checksum = 0;
    memset(ack_packet.payload, 0, 20);
    
    /* 如果是NAK，设置特殊标记 */
    if (is_nak) {
        ack_packet.acknum = -ack_num - 1; /* 负值表示NAK */
    }
    
    ack_packet.checksum = compute_checksum(&ack_packet);
    
    tolayer3(1, ack_packet);
    if (is_nak) {
        printf("B发送NAK: seq=%d\n", ack_num);
    } else {
        printf("B发送ACK: seq=%d\n", ack_num);
    }
}

/* 检查序列号是否在发送窗口内 */
int in_send_window(int seq_num) {
    if (send_base <= seq_num && seq_num < send_base + WINDOW_SIZE) {
        return 1;
    }
    if (send_base + WINDOW_SIZE >= MAX_SEQ && 
        seq_num < (send_base + WINDOW_SIZE) % MAX_SEQ) {
        return 1;
    }
    return 0;
}

/* 检查序列号是否在接收窗口内 */
int in_recv_window(int seq_num) {
    if (recv_base <= seq_num && seq_num < recv_base + WINDOW_SIZE) {
        return 1;
    }
    if (recv_base + WINDOW_SIZE >= MAX_SEQ && 
        seq_num < (recv_base + WINDOW_SIZE) % MAX_SEQ) {
        return 1;
    }
    return 0;
}

/* A_output - 发送方应用层调用 */
void A_output(struct msg message) {
    /* 缓存消息 */
    int buffer_index = next_seq % MAX_SEQ;
    send_buffer[buffer_index] = message;
    
    /* 如果窗口有空闲，立即发送 */
    if (next_seq < send_base + WINDOW_SIZE) {
        send_packet(next_seq);
        acked[next_seq] = 0; /* 标记为未确认 */
        next_seq = (next_seq + 1) % MAX_SEQ;
    } else {
        printf("窗口已满，分组 %d 被缓存\n", next_seq);
        next_seq = (next_seq + 1) % MAX_SEQ;
    }
}

/* A_input - 发送方网络层调用 */
void A_input(struct pkt packet) {
    if (is_corrupt(&packet)) {
        printf("A收到损坏的ACK\n");
        return;
    }
    
    int ack_num = packet.acknum;
    
    /* 处理NAK (负值表示NAK) */
    if (ack_num < 0) {
        int nak_seq = -ack_num - 1;
        printf("A收到NAK，重传分组: seq=%d\n", nak_seq);
        if (in_send_window(nak_seq) && !acked[nak_seq]) {
            send_packet(nak_seq);
        }
        return;
    }
    
    /* 处理正常ACK */
    printf("A收到ACK: seq=%d\n", ack_num);
    
    if (in_send_window(ack_num)) {
        acked[ack_num] = 1; /* 标记为已确认 */
        
        /* 移动窗口基序号到第一个未确认的分组 */
        while (acked[send_base]) {
            acked[send_base] = 0; /* 重置状态 */
            send_base = (send_base + 1) % MAX_SEQ;
            printf("发送窗口移动到: base=%d\n", send_base);
        }
        
        /* 停止定时器如果没有未确认的分组 */
        int has_unacked = 0;
        for (int i = 0; i < WINDOW_SIZE; i++) {
            int seq = (send_base + i) % MAX_SEQ;
            if (seq < next_seq && !acked[seq]) {
                has_unacked = 1;
                break;
            }
        }
        
        if (!has_unacked) {
            stoptimer(0);
        }
    }
}

/* A_timerinterrupt - 发送方超时处理 */
void A_timerinterrupt() {
    printf("超时，检查未确认的分组\n");
    
    /* 检查所有在窗口中且未确认的分组 */
    for (int i = 0; i < WINDOW_SIZE; i++) {
        int seq = (send_base + i) % MAX_SEQ;
        if (seq < next_seq && !acked[seq]) {
            /* 检查是否真的超时 */
            if (time - timer_start[seq] > TIMEOUT_INTERVAL) {
                printf("重传超时分组: seq=%d\n", seq);
                send_packet(seq);
            }
        }
    }
    
    /* 重启定时器 */
    starttimer(0, TIMEOUT_INTERVAL);
}

/* B_input - 接收方网络层调用 */
void B_input(struct pkt packet) {
    if (is_corrupt(&packet)) {
        printf("B收到损坏的分组\n");
        return;
    }
    
    int seq_num = packet.seqnum;
    printf("B收到分组: seq=%d, 期望=%d\n", seq_num, recv_base);
    
    /* 检查是否在接收窗口内 */
    if (in_recv_window(seq_num)) {
        if (!received[seq_num]) {
            /* 缓存分组 */
            strncpy(recv_buffer[seq_num].data, packet.payload, 20);
            received[seq_num] = 1;
            printf("B缓存分组: seq=%d\n", seq_num);
        }
        
        /* 发送该分组的ACK */
        send_ack(seq_num, 0);
        
        /* 检查是否可以交付数据 */
        while (received[recv_base]) {
            /* 交付到应用层 */
            tolayer5(1, recv_buffer[recv_base].data);
            printf("B交付分组: seq=%d\n", recv_base);
            
            received[recv_base] = 0; /* 重置状态 */
            recv_base = (recv_base + 1) % MAX_SEQ;
        }
    } else {
        /* 分组不在窗口内，发送NAK请求重传 */
        printf("B收到窗口外分组: seq=%d, 发送NAK\n", seq_num);
        send_ack(seq_num, 1);
    }
}

/* B_timerinterrupt - 接收方定时器（可选，用于清理等） */
void B_timerinterrupt() {
    /* SR接收方通常不需要定时器，但可以用于其他维护任务 */
    starttimer(1, 1000.0); /* 简单的保持定时器 */
}

/* B_output - 双向传输时使用 */
void B_output(struct msg message) {
    /* 对于单向传输，这个函数不会被调用 */
    printf("B_output called - not used in unidirectional transfer\n");
}

/* 初始化函数 */
void A_init() {
    send_base = 0;
    next_seq = 0;
    memset(acked, 0, sizeof(acked));
    memset(timer_start, 0, sizeof(timer_start));
    printf("A初始化完成 - SR协议，窗口大小=%d\n", WINDOW_SIZE);
}

void B_init() {
    recv_base = 0;
    memset(received, 0, sizeof(received));
    printf("B初始化完成 - SR协议，窗口大小=%d\n", WINDOW_SIZE);
}
