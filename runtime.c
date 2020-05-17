#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include "gc.h"

enum type {
    INT, LONG, FLOAT, BOOLEAN, STRING, LIST, TUPLE, DICT
};

struct list
{
    long size;
    struct value *pt;
};


struct value {
    enum type type;
    union {
        int int_value;
        long long_value;
        float float_value;
        bool bool_value;
        char *string_value;
        struct list *list_value;
        // tuple *tuple_value;
        // dict *dict_value;
        // struct {
        //     klass *klass;
        //     size_t attrs_size;
        //     hash_table *attrs;
        // };
    };
};

void error(char *msg);

long input()
{
    long val;
    scanf("%ld", &val);
    return val;
}

void print_int_nl(long val)
{
    printf("%ld\n", val);
}

// Boxing functions
struct value *box_int(int n) 
{
    struct value *p = GC_malloc(sizeof(struct value));
    p->type = INT;
    p->int_value = n;
    return p;
}

int unbox_int(struct value *p)
{
    if (p->type == INT)
        return p->int_value;
    error("tried to unbox_int a non-integer value.");
}

struct value *box_long(long n) 
{
    struct value *p = GC_malloc(sizeof(struct value));
    p->type = LONG;
    p->long_value = n;
    return p;
}

long unbox_long(struct value *p)
{
    if (p->type == LONG)
        return p->long_value;
    error("tried to unbox_int a non-integer value.");
}

struct value *box_bool(bool b)
{
    struct value *p = GC_MALLOC(sizeof(struct value));
    p->type = BOOLEAN;
    p->bool_value = b;
    return p;
}

bool unbox_bool(struct value *p)
{
    if (p->type == BOOLEAN)
        return p->bool_value;
    error("tried to unbox_bool a non-bool value.");
}

struct value *box_float(float f)
{
    struct value *p = GC_MALLOC(sizeof(struct value));
    p->type = FLOAT;
    p->float_value = f;
    return p;
}

float unbox_float(struct value *p)
{
    if (p->type == FLOAT)
        return p->float_value;
    error("Tried to unbox_float a non-float value.");
}

struct value *create_array()
{
    struct value *p = GC_MALLOC(sizeof(struct value));
    struct list *l = GC_MALLOC(sizeof(struct list) * 10); // start with size 10
    p->type = LIST;
    p->list_value = l;
}

struct value *access_array(struct value *p, long index)
{
    if (p->type == LIST) {
        l = p->list_value;
        if (index < l->size)
            return l->pt[index];
        error("array index out of bound");
    }
    error("Tring to access a non-list or dict value.");
}

long len(struct value *p)
{
    if (p->type == LIST)
        return p->list_value->size; 
    error("Object has no len()");
}

void error(char *msg)
{
    printf("%s", msg);
    exit(100);
}