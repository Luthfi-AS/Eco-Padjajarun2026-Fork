from django.contrib import admin
from .models import TicketCategory, Order


@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "quota", "is_active")
    search_fields = ("name",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_code",
        "participant_name",
        "ticket",
        "payment_status",
        "checked_in",
        "created_at",
    )
    list_filter = ("payment_status", "checked_in", "ticket")
    search_fields = ("order_code", "participant_name", "participant_email")
    readonly_fields = ("order_code", "qr_code", "created_at")
    actions = ["mark_paid", "mark_checked_in"]

    def mark_paid(self, request, queryset):
        for order in queryset:
            order.payment_status = "PAID"
            order.save()
        self.message_user(request, "Order terpilih berhasil diubah menjadi PAID.")

    mark_paid.short_description = "Tandai sebagai PAID"

    def mark_checked_in(self, request, queryset):
        queryset.update(checked_in=True)
        self.message_user(request, "Order terpilih berhasil check-in.")

    mark_checked_in.short_description = "Tandai check-in"
