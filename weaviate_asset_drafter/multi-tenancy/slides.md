# Multi-Tenancy in Weaviate

---

## What is Multi-Tenancy?

Multi-tenancy provides **data isolation within a single collection** by partitioning data into separate shards, where each shard holds data for one tenant.

---

### Key Concept
- Each tenant is stored on a **dedicated shard**
- Data from one tenant is **completely isolated** from others
- Multiple tenants share the same collection schema and indexes
- Each tenant has its own **high-performance vector index**

---

### Architecture
```
Single Collection
├── Tenant A Shard
│   ├── Indexes
│   └── Object Store
├── Tenant B Shard
│   ├── Indexes
│   └── Object Store
└── Tenant C Shard
    ├── Indexes
    └── Object Store
```

**Perfect for:** SaaS platforms, multi-customer systems, and applications serving many users with isolated data needs.

---

## Practical Problems Addressed

Multi-tenancy solves **critical scalability and operational challenges**:

---

### Problem: Resource Inefficiency
- **Without multi-tenancy:** Creating separate collections for each tenant requires duplicate indexes, schemas, and storage overhead
- **With multi-tenancy:** All tenants share one collection definition, dramatically reducing resource consumption

---

### Problem: Operational Complexity
- **Without multi-tenancy:** Updating schema definitions requires manual updates to each collection individually
- **With multi-tenancy:** Changes apply universally to all tenants automatically

---

### Problem: Scale Limitations
- **Without multi-tenancy:** Managing 1,000s of collections becomes impossible
- **With multi-tenancy:** You can support **1M+ concurrently active tenants** with just 20-30 nodes (50,000+ shards per node)

---

### Problem: Deletion Performance
- **Without multi-tenancy:** Deleting data affects shared indexes
- **With multi-tenancy:** Deleting a tenant deletes its entire shard instantly—fast and isolated

---

## Use Cases & Configuration

### Real-World Use Cases
- **SaaS Platforms:** Separate customer data (e.g., Slack workspaces, Notion accounts)
- **Multi-Project Applications:** Store project data without collection proliferation
- **Multi-Tenant Marketplaces:** Sellers' products remain isolated
- **Enterprise Systems:** Department-specific data isolation

---

### Collection Definition (Python)

```python
from weaviate.classes.config import Configure

# Enable multi-tenancy with auto-tenant creation
multi_collection = client.collections.create(
    name="SaaSProducts",
    multi_tenancy_config=Configure.multi_tenancy(
        enabled=True,
        auto_tenant_creation=True  # Automatically create tenants on first insert
    ),
    properties=[
        {
            "name": "product_name",
            "data_type": "text"
        },
        {
            "name": "price",
            "data_type": "number"
        }
    ]
)
```

---

### Tenant Creation

```python
from weaviate.classes.tenants import Tenant

# Manually create tenants
multi_collection.tenants.create(
    tenants=[
        Tenant(name="customer_acme"),
        Tenant(name="customer_globex"),
        Tenant(name="customer_initech")
    ]
)

# List all tenants
tenants = multi_collection.tenants.get()
print(tenants)
```

---

## Data Ingestion & Queries

---

### Inserting Data (Tenant-Specific)

```python
# Get collection reference for a specific tenant
multi_tenant = multi_collection.with_tenant("customer_acme")

# Insert object into that tenant
object_id = multi_tenant.data.insert(
    properties={
        "product_name": "Enterprise Software Suite",
        "price": 9999.99
    }
)
```

---

### Querying Data (Tenant-Specific)

```python
# Query only customer_acme's data
multi_tenant_acme = multi_collection.with_tenant("customer_acme")

# Fetch objects for this tenant
result = multi_tenant_acme.query.fetch_objects(limit=10)

for obj in result.objects:
    print(obj.properties)

# Data from other tenants is NOT visible
```

---

### Key Points
- **Every query MUST specify a tenant** using `.with_tenant()`
- Queries are automatically filtered to that tenant's shard
- No cross-tenant data leakage is possible
- Query performance is optimized per tenant

---

## Best Practices

---

### ✅ Do This

1. **Use Consistent Tenant Names**
   - Use lowercase alphanumeric characters, hyphens, underscores
   - Example: `customer_acme_corp`, `project_001`
   - Avoids accidental duplicate tenants from typos

---

2. **Plan Your Schema Carefully**
   - All tenants share the same schema
   - Add all properties you'll need upfront
   - You can't customize properties per tenant

---

3. **Manage Tenant States**
   - Set unused tenants to `INACTIVE` to save memory
   - Tenants stored on disk can be quickly reactivated
   - `OFFLOADED` tenants save resources for long-term storage

---

4. **Monitor Tenant Scalability**
   - Track the number of active tenants per node
   - Balance load across your cluster
   - Weaviate auto-distributes new tenants to nodes with least usage

---

### ❌ Avoid This

- **Don't create separate collections** if you have >20 datasets—use multi-tenancy instead
- **Don't assume automatic access control**—implement fine-grained authorization separately
- **Don't forget to specify tenants** in queries—always use `.with_tenant()`
- **Don't mix multi-tenancy with cross-tenant queries**—data isolation is strict by design
- **Don't use inconsistent tenant naming** (e.g., "TenantOne" vs "tenantone")—creates duplicates

---

### Performance Tips
- Each tenant has a dedicated, high-performance index
- Query speeds are equivalent to having a single-tenant system
- Fast deletion of entire tenant datasets (deletes the shard)
- Backup only `ACTIVE` tenants before migration
