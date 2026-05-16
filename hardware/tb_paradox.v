// tb_paradox.v – Testbench for paradox accelerator
`timescale 1ns / 1ps

module tb_paradox();
    reg clk, rst_n;
    reg [31:0] addr, wr_data;
    reg wr_en;
    wire [31:0] rd_data;
    wire rd_valid, interrupt;
    
    paradox_accelerator uut (
        .clk(clk), .rst_n(rst_n),
        .addr(addr), .wr_data(wr_data), .wr_en(wr_en),
        .rd_data(rd_data), .rd_valid(rd_valid),
        .interrupt(interrupt)
    );
    
    always #5 clk = ~clk;
    
    task write_reg(input [7:0] reg_addr, input [31:0] data);
        @(posedge clk);
        addr <= reg_addr;
        wr_data <= data;
        wr_en <= 1;
        @(posedge clk);
        wr_en <= 0;
    endtask
    
    task read_reg(input [7:0] reg_addr, output [31:0] data);
        @(posedge clk);
        addr <= reg_addr;
        wr_en <= 0;
        @(posedge clk);
        data <= rd_data;
    endtask
    
    initial begin
        clk = 0;
        rst_n = 0;
        addr = 0;
        wr_data = 0;
        wr_en = 0;
        #20 rst_n = 1;
        
        // Test generate mode
        write_reg(8'h10, 32'd3);      // length = 3
        write_reg(8'h08, 32'h1234);   // seed
        write_reg(8'h00, 32'd1);      // start generate (mode=0)
        
        wait(interrupt);
        read_reg(8'h0C, result);
        $display("Generated paradox code: %0d", result);
        
        // Test verify mode (with correct response)
        write_reg(8'h0C, 32'd42);     // pretend response (should match)
        write_reg(8'h00, 32'd3);      // start verify (mode=1, bit1=1, bit0=1)
        
        wait(interrupt);
        read_reg(8'h04, status);
        if (status[2]) $display("Verification PASSED");
        else $display("Verification FAILED");
        
        $finish;
    end
endmodule