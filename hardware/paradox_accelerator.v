// paradox_accelerator_full.v
// Suportă prime_interval, causal_loop, self_referential

module paradox_accelerator_full (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [31:0] addr,
    input  wire [31:0] wr_data,
    input  wire        wr_en,
    output reg  [31:0] rd_data,
    output reg         rd_valid,
    output reg         interrupt
);

    // Registre
    reg [31:0] control;
    reg [31:0] status;
    reg [31:0] seed_reg;
    reg [31:0] result_reg;
    reg [31:0] length_reg;
    reg [31:0] timebase_reg;
    reg [31:0] loop_value_reg;
    
    // Internal state
    reg        busy;
    reg [1:0]  paradox_type;
    reg [31:0] prime_seq [0:7];
    reg [3:0]  seq_idx;
    reg [31:0] timer;
    reg        done;
    reg        valid;
    
    // Prime table (first 32 primes)
    localparam [31:0] PRIMES [0:31] = '{
        2,3,5,7,11,13,17,19,23,29,
        31,37,41,43,47,53,59,61,67,71,
        73,79,83,89,97,101,103,107,109,113,
        127,131
    };
    
    // LFSR pentru selecție pseudo-aleatoare
    reg [31:0] lfsr;
    wire lfsr_next = {lfsr[30:0], lfsr[31] ^ lfsr[21] ^ lfsr[1] ^ lfsr[0]};
    
    // ------------------------------------------------------------------
    // Scriere registre
    // ------------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            control <= 32'd0;
            seed_reg <= 32'd0;
            length_reg <= 32'd3;
            timebase_reg <= 32'd1000000;
            loop_value_reg <= 32'd0;
            result_reg <= 32'd0;
        end else if (wr_en) begin
            case (addr[7:0])
                8'h00: control <= wr_data;
                8'h08: seed_reg <= wr_data;
                8'h10: length_reg <= wr_data;
                8'h14: timebase_reg <= wr_data;
                8'h18: loop_value_reg <= wr_data;
                8'h0C: result_reg <= wr_data;   // pentru verificare
            endcase
        end
    end
    
    // ------------------------------------------------------------------
    // Citire registre
    // ------------------------------------------------------------------
    always @(posedge clk) begin
        rd_valid <= 1'b1;
        case (addr[7:0])
            8'h00: rd_data <= control;
            8'h04: rd_data <= status;
            8'h08: rd_data <= seed_reg;
            8'h0C: rd_data <= result_reg;
            8'h10: rd_data <= length_reg;
            8'h14: rd_data <= timebase_reg;
            8'h18: rd_data <= loop_value_reg;
            default: rd_data <= 32'd0;
        endcase
    end
    
    // ------------------------------------------------------------------
    // FSM unificată
    // ------------------------------------------------------------------
    localparam IDLE = 0, GEN_PRIME = 1, WAIT_PRIME = 2, 
               CAUSAL_LOOP = 3, SELF_REF = 4, DONE = 5;
    reg [2:0] state;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            busy <= 0;
            done <= 0;
            valid <= 0;
            interrupt <= 0;
            lfsr <= 32'hDEADBEEF;
            seq_idx <= 0;
            timer <= 0;
        end else begin
            case (state)
                IDLE: begin
                    interrupt <= 0;
                    if (control[0] && !busy) begin
                        busy <= 1;
                        paradox_type <= control[2:1];
                        done <= 0;
                        valid <= 0;
                        // Reset LFSR cu seed
                        lfsr <= (seed_reg != 0) ? seed_reg : 32'hCAFEBABE;
                        seq_idx <= 0;
                        timer <= 0;
                        // Alege submașina în funcție de tip
                        case (control[2:1])
                            2'b00: state <= GEN_PRIME;   // prime_interval
                            2'b01: state <= CAUSAL_LOOP;  // causal_loop
                            2'b10: state <= SELF_REF;     // self_referential
                            default: state <= DONE;
                        endcase
                    end
                end
                
                // ----------------------------------------------
                // Prime interval generation / verification
                // ----------------------------------------------
                GEN_PRIME: begin
                    if (seq_idx < length_reg[4:0]) begin
                        lfsr <= lfsr_next;
                        prime_seq[seq_idx] <= PRIMES[lfsr[4:0]];
                        seq_idx <= seq_idx + 1;
                    end else begin
                        // Modul 0 = generare (output xor din secvență)
                        if (control[1] == 0) begin
                            result_reg <= prime_seq[0] ^ prime_seq[1] ^ prime_seq[2] ^
                                          (length_reg > 3 ? prime_seq[3] : 0);
                            valid <= 1;
                            state <= DONE;
                        end else begin
                            // Modul 1 = verificare: așteaptă intervale
                            seq_idx <= 0;
                            timer <= 0;
                            state <= WAIT_PRIME;
                        end
                    end
                end
                
                WAIT_PRIME: begin
                    if (timer < prime_seq[seq_idx] * timebase_reg) begin
                        timer <= timer + 1;
                    end else begin
                        if (prime_seq[seq_idx] == result_reg) begin
                            seq_idx <= seq_idx + 1;
                            timer <= 0;
                            if (seq_idx + 1 >= length_reg) begin
                                valid <= 1;
                                state <= DONE;
                            end
                        end else begin
                            valid <= 0;
                            state <= DONE;
                        end
                    end
                end
                
                // ----------------------------------------------
                // Causal loop: result = f(seed, loop_value)
                // ----------------------------------------------
                CAUSAL_LOOP: begin
                    // Implementare simplă: result = seed XOR loop_value
                    // Apoi loop_value devine result (buclă)
                    if (control[1] == 0) begin
                        // Generare: un cod care depinde de el însuși
                        result_reg <= seed_reg ^ loop_value_reg;
                        valid <= 1;
                        state <= DONE;
                    end else begin
                        // Verificare: result_reg trebuie să fie seed XOR loop_value
                        valid <= (result_reg == (seed_reg ^ loop_value_reg));
                        state <= DONE;
                    end
                end
                
                // ----------------------------------------------
                // Self-referential: "Această valoare este X"
                // ----------------------------------------------
                SELF_REF: begin
                    // Folosim o funcție hash simplă: seed XOR (seed >> 16)
                    if (control[1] == 0) begin
                        result_reg <= seed_reg ^ (seed_reg >> 16);
                        valid <= 1;
                        state <= DONE;
                    end else begin
                        // Verificare: seed_reg trebuie să fie rezultatul corect
                        valid <= (seed_reg == (result_reg ^ (result_reg >> 16)));
                        state <= DONE;
                    end
                end
                
                DONE: begin
                    busy <= 0;
                    done <= 1;
                    interrupt <= 1;
                    state <= IDLE;
                    control[0] <= 0;   // clear start
                end
            endcase
        end
    end
    
    // Status register
    always @(posedge clk) begin
        status <= {28'd0, valid, done, busy};
        if (state == DONE) begin
            done <= 0;
            valid <= 0;
        end
    end

endmodule