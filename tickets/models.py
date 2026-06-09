import uuid
from django.contrib.auth.models import User
from django.db import models
class TicketCategory(models.Model):
    name=models.CharField(max_length=120); description=models.TextField(); price=models.PositiveIntegerField(); quota=models.PositiveIntegerField(default=100); is_active=models.BooleanField(default=True)
    def __str__(self): return self.name
    @property
    def sold(self): return self.orders.filter(payment_status='PAID').count()
    @property
    def remaining(self): return max(self.quota-self.sold,0)
class Order(models.Model):
    PAYMENT_STATUS=[('PENDING','Pending'),('PAID','Paid'),('FAILED','Failed'),('EXPIRED','Expired'),('REFUNDED','Refunded')]
    order_code=models.CharField(max_length=40,unique=True,editable=False); user=models.ForeignKey(User,on_delete=models.CASCADE); ticket=models.ForeignKey(TicketCategory,related_name='orders',on_delete=models.PROTECT)
    participant_name=models.CharField(max_length=120); participant_email=models.EmailField(); participant_phone=models.CharField(max_length=30); payment_status=models.CharField(max_length=20,choices=PAYMENT_STATUS,default='PENDING')
    qr_code=models.ImageField(upload_to='qr_codes/',blank=True,null=True); checked_in=models.BooleanField(default=False); created_at=models.DateTimeField(auto_now_add=True)
    def save(self,*args,**kwargs):
        if not self.order_code: self.order_code='ECO-'+uuid.uuid4().hex[:10].upper()
        super().save(*args,**kwargs)
    def __str__(self): return self.order_code
