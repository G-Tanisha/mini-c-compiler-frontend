// ============================================================
// test_program.mc  —  Mini-C feature exercise
// ============================================================

// --- int and float declarations with initializers ----------
int x = 5;
float y = 10.5;
int z;

// --- single-dimensional int array --------------------------
int list[10];

// --- arithmetic expressions --------------------------------
z = x + 2;
y = y * 2.0;

// --- array element assignments -----------------------------
list[0] = x;
list[1] = z;

// --- if-else -----------------------------------------------
if (x < 10) {
    print(x);
} else {
    print(z);
}

// --- while loop --------------------------------------------
int i = 0;
while (i < 5) {
    list[i] = i;
    print(list[i]);
    i = i + 1;
}

// --- for loop (loop variable scoped to the for header) -----
int sum = 0;
for (int j = 0; j < 5; j = j + 1) {
    sum = sum + j;
}
print(sum);

// --- float arithmetic / nested expression ------------------
float result = (y + 1.0) * 2.0 - 3.5;
print(result);

// --- block scoping demo (inner x shadows outer x) ----------
{
    int x = 99;
    print(x);
}
print(x);

// --- INTENTIONAL TYPE ERROR (uncomment to trigger) ---------
// int bad = y;   // ERROR: cannot assign float to int variable 'bad'
