#!/usr/bin/python
#coding=utf8
from pycomm.utils.storage import Const


class PaiPaiRequestDealState(Const):
    DS_UNKNOWN = ('DS_UNKNOWN', "系统处理中,未知状态")
    DS_WAIT_BUYER_PAY = ('DS_WAIT_BUYER_PAY', "等待买家付款")
    DS_WAIT_SELLER_DELIVERY = ('DS_WAIT_SELLER_DELIVERY', "买家已付款,等待卖家发货")
    DS_WAIT_BUYER_RECEIVE = ('DS_WAIT_BUYER_RECEIVE', "商家已发货，等待买家收货")    
    DS_DEAL_END_NORMAL = ('DS_DEAL_END_NORMAL', "交易成功")
    DS_DEAL_CANCELLED = ('DS_DEAL_CANCELLED', "订单取消")      
    DS_SYSTEM_HALT = ('DS_SYSTEM_HALT', "系统暂停订单")      
    DS_SYSTEM_PAYING = ('DS_SYSTEM_PAYING', "系统打款中")     
    DS_DEAL_REFUNDING = ('DS_DEAL_REFUNDING', "退款处理中")  


#    STATE_COD_WAIT_SHIP：货到付款等待发货
#    STATE_COD_SHIP_OK：货到付款已发货
#    STATE_COD_SIGN：货到付款已签收
#    STATE_COD_REFUSE：货到付款拒签
#    STATE_COD_SUCESS：货到付款成功(已打款)
#    STATE_COD_CANCEL：货到付款取消(关闭or 拒签后关闭)

class PaiPaiResponseDealState(Const):
    DS_WAIT_BUYER_PAY = ('DS_WAIT_BUYER_PAY', '等待买家付款')
    DS_WAIT_SELLER_DELIVERY = ('DS_WAIT_SELLER_DELIVERY', '等待卖家发货(说明卖家已付款，卖家还没有发货)')
    DS_BUYER_PAID_CFT = ('DS_BUYER_PAID_CFT', '买家已生成财付通支付单号')
    DS_WAIT_BUYER_RECEIVE = ('DS_WAIT_BUYER_RECEIVE', '卖家已发货(既是：等待买家确认收货)')
    DS_DEAL_CANCELLED = ('DS_DEAL_CANCELLED', '订单取消')
    DS_DEAL_REFUNDING = ('DS_DEAL_REFUNDING', '退款处理中')
    DS_DEAL_SHIPPING_PREPARE = ('DS_DEAL_SHIPPING_PREPARE', '卖家配货中')
    DS_DEAL_END_REFUND = ('DS_DEAL_END_REFUND', '订单退款结束')
    DS_DEAL_END_NORMAL = ('DS_DEAL_END_NORMAL', '交易成功')
    DS_BUYER_EVALUATED = ('DS_BUYER_EVALUATED', '买家已评价')
    DS_REFUND_START = ('DS_REFUND_START', '开始退款流程')
    DS_REFUND_WAIT_BUYER_DELIVERY = ('DS_REFUND_WAIT_BUYER_DELIVERY', '等待买家发送退货')
    DS_REFUND_WAIT_SELLER_RECEIVE = ('DS_REFUND_WAIT_SELLER_RECEIVE', '等待卖家确认收货')
    DS_REFUND_WAIT_SELLER_AGREE = ('DS_REFUND_WAIT_SELLER_AGREE', '等待卖家同意退款')
    DS_REFUND_OK = ('DS_REFUND_OK', '退款成功')
    DS_REFUND_CANCEL = ('DS_REFUND_CANCEL', '退款取消')
    DS_REFUND_ALL_WAIT_SELLER_AGREE = ('DS_REFUND_ALL_WAIT_SELLER_AGREE', '等待卖家同意全额退款')
    DS_REFUND_WAIT_MODIFY = ('DS_REFUND_WAIT_MODIFY', '等待买家修改退款申请')
    DS_REFUND_ALL_CANCEL = ('DS_REFUND_ALL_CANCEL', '全额退款取消')
    DS_REFUND_ALL_OK = ('DS_REFUND_ALL_OK', '全额退款成功')
    DS_TIMEOUT_BUYER_RECEIVE = ('DS_TIMEOUT_BUYER_RECEIVE', '等待买家确认收货超时')
    DS_TIMEOUT_SELLER_RECEIVE = ('DS_TIMEOUT_SELLER_RECEIVE', '等待卖家确认收货超时')
    DS_TIMEOUT_SELLER_PASS_RETURN = ('DS_TIMEOUT_SELLER_PASS_RETURN', '等待卖家响应买家退货请求超时')
    DS_TIMEOUT_SELLER_PASS_REFUND_ALL = ('DS_TIMEOUT_SELLER_PASS_REFUND_ALL', '等待卖家确认全额退款超时')
    DS_CLOSED = ('DS_CLOSED', '订单已关闭')
    DS_UNKNOWN = ('DS_UNKNOWN', '系统处理中')

class PaiPaiDealType(Const):
    ALL = ('0', '全部')
    PAIPAI = ('1', '拍拍')
    STREET = ('4', '店铺街')
